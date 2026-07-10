from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

from ingest_cps_pdfs import CODE_TO_KR, clean_text, is_noisy


DEFAULT_CPS_DIR = Path("/Users/kimjaeyoung/Downloads/CPS(kor)")
DEFAULT_CSV = Path("KODA_cps_pdf_ocr_coverage.csv")
DEFAULT_MD = Path("docs/cps_ocr_coverage.md")


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


def markdown_report(df: pd.DataFrame, cps_dir: Path) -> str:
    total_pages = int(df["Pages"].sum()) if not df.empty else 0
    readable_pages = int(df["Readable_Pages"].sum()) if not df.empty else 0
    ocr_targets = int(df["OCR_Target_Pages"].sum()) if not df.empty else 0
    image_only = df.loc[df["Readable_Pages"] == 0, "Country_Code"].tolist()
    partial = df.loc[(df["Readable_Pages"] > 0) & (df["OCR_Target_Pages"] > 0), "Country_Code"].tolist()

    lines = [
        "# CPS OCR Coverage Report",
        "",
        f"- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Source directory: `{cps_dir}`",
        f"- CPS PDFs checked: {len(df)}",
        f"- Readable text-layer pages: {readable_pages}/{total_pages}",
        f"- OCR target pages: {ocr_targets}",
        f"- Image-only PDFs requiring OCR: {', '.join(image_only) if image_only else 'None'}",
        f"- Partial text-layer PDFs: {', '.join(partial) if partial else 'None'}",
        "",
        "## Interpretation",
        "",
        "The RAG corpus already uses all pages that expose a readable text layer. "
        "Image-only CPS PDFs are explicitly flagged instead of silently treated as missing evidence. "
        "Run `scripts/ocr_cps_pdfs.py` with Tesseract Korean OCR installed to regenerate `KODA_cps_pdf_chunks.csv` with OCR-backed chunks.",
        "",
        "## Per-PDF Coverage",
        "",
        "| Code | Country | Pages | Readable | OCR Target | Ratio | Status |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for _, row in df.iterrows():
        lines.append(
            f"| {row['Country_Code']} | {row['Country_KR']} | {int(row['Pages'])} | "
            f"{int(row['Readable_Pages'])} | {int(row['OCR_Target_Pages'])} | "
            f"{float(row['Readable_Page_Ratio']):.1%} | {row['Coverage_Status']} |"
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
    args = parser.parse_args()

    cps_dir = Path(args.input).expanduser()
    if not cps_dir.exists():
        raise FileNotFoundError(cps_dir)

    df = pd.DataFrame(coverage_rows(cps_dir))
    if df.empty:
        raise RuntimeError(f"No PDF files found in {cps_dir}")

    csv_path = Path(args.csv)
    md_path = Path(args.md)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    md_path.write_text(markdown_report(df, cps_dir), encoding="utf-8")
    print(f"wrote {csv_path.resolve()} rows={len(df)}")
    print(f"wrote {md_path.resolve()}")


if __name__ == "__main__":
    main()
