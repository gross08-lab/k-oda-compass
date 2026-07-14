from __future__ import annotations

import argparse
import hashlib
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

from ingest_cps_pdfs import CODE_TO_KR, clean_text, is_noisy


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CPS_DIR = Path(os.getenv("KODA_CPS_PDF_DIR", ROOT / "data" / "cps_pdfs"))
DEFAULT_CSV = Path("KODA_cps_pdf_ocr_coverage.csv")
DEFAULT_MD = Path("docs/cps_ocr_coverage.md")
DEFAULT_CHUNKS = Path("KODA_cps_pdf_chunks.csv")
DEFAULT_MANIFEST = Path("data/cps_document_manifest.csv")
DEFAULT_PAGE_CACHE = Path("data/cps_page_text.csv")


def page_texts(pdf_path: Path) -> list[str]:
    reader = PdfReader(str(pdf_path))
    return [clean_text(page.extract_text() or "") for page in reader.pages]


def coverage_rows(cps_dir: Path) -> list[dict]:
    rows: list[dict] = []
    for pdf_path in sorted(cps_dir.glob("*.pdf")):
        code = pdf_path.stem.upper()
        texts = page_texts(pdf_path)
        readable = [text for text in texts if not is_noisy(text)]
        chars = sum(len(text) for text in readable)
        pages = len(texts)
        readable_pages = len(readable)
        if readable_pages == 0:
            status = "Image-only - OCR required"
        elif readable_pages < pages:
            status = "Partial text layer"
        else:
            status = "Text layer OK"
        rows.append(
            {
                "Country_Code": code,
                "Country_KR": CODE_TO_KR.get(code, code),
                "PDF_File": pdf_path.name,
                "Pages": pages,
                "Readable_Pages": readable_pages,
                "OCR_Target_Pages": pages - readable_pages,
                "Readable_Page_Ratio": round(readable_pages / pages, 4) if pages else 0,
                "Extracted_Chars": chars,
                "Coverage_Status": status,
            }
        )
    return rows


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def add_search_coverage(
    df: pd.DataFrame, chunk_path: Path, page_cache_path: Path
) -> pd.DataFrame:
    if not chunk_path.exists():
        for column in ("OCR_Completed_Pages", "Searchable_Pages", "Searchable_Chunks"):
            df[column] = 0
        df["Search_Status"] = "Not indexed"
        return df
    chunks = pd.read_csv(chunk_path)
    chunks["Is_OCR"] = chunks["Extraction_Method"].astype(str).str.contains("-ocr:", regex=False)
    summary = chunks.groupby("PDF_File").agg(
        Searchable_Pages=("Page", "nunique"),
        Searchable_Chunks=("Chunk_ID", "nunique"),
    )
    ocr = chunks.loc[chunks["Is_OCR"]].groupby("PDF_File")["Page"].nunique().rename("OCR_Completed_Pages")
    summary = summary.join(ocr, how="left").fillna({"OCR_Completed_Pages": 0}).reset_index()
    merged = df.merge(summary, on="PDF_File", how="left")
    for column in ("OCR_Completed_Pages", "Searchable_Pages", "Searchable_Chunks"):
        merged[column] = pd.to_numeric(merged[column], errors="coerce").fillna(0).astype(int)
    merged["Search_Status"] = merged["Searchable_Chunks"].gt(0).map({True: "Searchable", False: "Not indexed"})
    if page_cache_path.exists():
        page_cache = pd.read_csv(page_cache_path)
        page_cache["Is_OCR"] = page_cache["Extraction_Method"].astype(str).str.contains(
            "-ocr:", regex=False
        )
        direct = (
            page_cache.loc[~page_cache["Is_OCR"]]
            .groupby("PDF_File")["Page"]
            .nunique()
            .rename("Direct_Extracted_Pages")
        )
        cached_ocr = (
            page_cache.loc[page_cache["Is_OCR"]]
            .groupby("PDF_File")["Page"]
            .nunique()
            .rename("Cached_OCR_Pages")
        )
        cached = direct.to_frame().join(cached_ocr, how="outer").fillna(0).reset_index()
        merged = merged.merge(cached, on="PDF_File", how="left")
    else:
        merged["Direct_Extracted_Pages"] = merged["Readable_Pages"]
        merged["Cached_OCR_Pages"] = merged["OCR_Completed_Pages"]
    for column in ("Direct_Extracted_Pages", "Cached_OCR_Pages"):
        merged[column] = pd.to_numeric(merged[column], errors="coerce").fillna(0).astype(int)
    merged["Unsearchable_Pages"] = (merged["Pages"] - merged["Searchable_Pages"]).clip(lower=0)
    return merged


def document_manifest(df: pd.DataFrame, cps_dir: Path) -> pd.DataFrame:
    rows = []
    for _, record in df.iterrows():
        pdf_path = cps_dir / str(record["PDF_File"])
        rows.append({
            "Country_Code": record["Country_Code"],
            "Country_KR": record["Country_KR"],
            "PDF_File": record["PDF_File"],
            "Pages": int(record["Pages"]),
            "File_Bytes": pdf_path.stat().st_size,
            "SHA256": file_sha256(pdf_path),
            "Text_Layer_Pages": int(record["Direct_Extracted_Pages"]),
            "OCR_Completed_Pages": int(record["OCR_Completed_Pages"]),
            "Searchable_Pages": int(record["Searchable_Pages"]),
            "Searchable_Chunks": int(record["Searchable_Chunks"]),
            "Search_Status": record["Search_Status"],
            "Source_Role": "현재 핵심 활용 · CPS 정책원문",
        })
    return pd.DataFrame(rows)


def markdown_report(df: pd.DataFrame, cps_dir: Path) -> str:
    total_pages = int(df["Pages"].sum()) if not df.empty else 0
    readable_pages = int(df["Direct_Extracted_Pages"].sum()) if not df.empty else 0
    ocr_targets = int(df["OCR_Target_Pages"].sum()) if not df.empty else 0
    ocr_completed = int(df["OCR_Completed_Pages"].sum()) if not df.empty else 0
    searchable_pages = int(df["Searchable_Pages"].sum()) if not df.empty else 0
    searchable_countries = int(df.loc[df["Search_Status"] == "Searchable", "Country_Code"].nunique())
    image_only = df.loc[df["Readable_Pages"] == 0, "Country_Code"].tolist()
    partial = df.loc[(df["Readable_Pages"] > 0) & (df["OCR_Target_Pages"] > 0), "Country_Code"].tolist()

    lines = [
        "# CPS OCR Coverage Report",
        "",
        f"- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Source directory: `{cps_dir.name}`",
        f"- CPS PDFs checked: {len(df)}",
        f"- Directly extracted searchable pages: {readable_pages}/{total_pages}",
        f"- pypdf-only OCR target diagnostic: {ocr_targets}",
        f"- OCR-completed searchable pages: {ocr_completed}",
        f"- Total searchable pages: {searchable_pages}",
        f"- Searchable countries: {searchable_countries}/{len(df)}",
        f"- Image-only PDFs requiring OCR: {', '.join(image_only) if image_only else 'None'}",
        f"- Partial text-layer PDFs: {', '.join(partial) if partial else 'None'}",
        "",
        "## Interpretation",
        "",
        "The RAG corpus already uses all pages that expose a readable text layer. "
        "Image-only CPS PDFs are explicitly flagged instead of silently treated as missing evidence. "
        "Run `scripts/ocr_cps_pdfs.py --engine auto` to use Tesseract when available or macOS Vision OCR on supported systems.",
        "",
        "## Per-PDF Coverage",
        "",
        "| Code | Country | Pages | Direct extract | OCR target diagnostic | OCR complete | Search pages | Chunks | Status |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for _, row in df.iterrows():
        lines.append(
            f"| {row['Country_Code']} | {row['Country_KR']} | {int(row['Pages'])} | "
            f"{int(row['Direct_Extracted_Pages'])} | {int(row['OCR_Target_Pages'])} | "
            f"{int(row['OCR_Completed_Pages'])} | {int(row['Searchable_Pages'])} | "
            f"{int(row['Searchable_Chunks'])} | {row['Search_Status']} |"
        )
    lines.extend(
        [
            "",
            "## Submission Note",
            "",
            "This report is included to make CPS evidence coverage auditable. "
            "The app can run from the committed CSV without parsing PDFs at startup, while OCR can be re-run offline when the source PDF set changes.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit CPS PDF text-layer coverage and OCR targets.")
    parser.add_argument("--input", default=str(DEFAULT_CPS_DIR), help="Directory containing CPS PDF files.")
    parser.add_argument("--csv", default=str(DEFAULT_CSV), help="Output coverage CSV.")
    parser.add_argument("--md", default=str(DEFAULT_MD), help="Output Markdown report.")
    parser.add_argument("--chunks", default=str(DEFAULT_CHUNKS), help="Searchable chunk CSV.")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="CPS document manifest CSV.")
    parser.add_argument("--page-cache", default=str(DEFAULT_PAGE_CACHE), help="Page extraction cache CSV.")
    args = parser.parse_args()

    cps_dir = Path(args.input).expanduser()
    if not cps_dir.exists():
        raise FileNotFoundError(cps_dir)

    df = add_search_coverage(
        pd.DataFrame(coverage_rows(cps_dir)), Path(args.chunks), Path(args.page_cache)
    )
    if df.empty:
        raise RuntimeError(f"No PDF files found in {cps_dir}")

    csv_path = Path(args.csv)
    md_path = Path(args.md)
    manifest_path = Path(args.manifest)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    md_path.write_text(markdown_report(df, cps_dir), encoding="utf-8")
    document_manifest(df, cps_dir).to_csv(manifest_path, index=False, encoding="utf-8-sig")
    print(f"wrote {csv_path.resolve()} rows={len(df)}")
    print(f"wrote {md_path.resolve()}")
    print(f"wrote {manifest_path.resolve()} rows={len(df)}")


if __name__ == "__main__":
    main()
