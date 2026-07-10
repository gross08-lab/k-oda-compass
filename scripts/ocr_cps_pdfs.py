from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

import pandas as pd

from ingest_cps_pdfs import (
    CODE_TO_KR,
    DEFAULT_CPS_DIR,
    DEFAULT_OUTPUT,
    chunk_page_text,
    extract_page_texts,
    is_noisy,
    clean_text,
    sector_tag,
)


BUNDLED_PDFTOPPM_CANDIDATES = [
    Path("/Users/kimjaeyoung/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pdftoppm"),
    Path("/Users/kimjaeyoung/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm"),
    Path("/Users/kimjaeyoung/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/bin/pdftoppm"),
    Path("/Users/kimjaeyoung/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/bin/pdftoppm"),
]


def find_binary(name: str, fallbacks: list[Path] | None = None) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    for fallback in fallbacks or []:
        if fallback.exists():
            return str(fallback)
    return None


def render_page(pdftoppm: str, pdf_path: Path, page_num: int, tmpdir: Path, dpi: int) -> Path:
    prefix = tmpdir / f"{pdf_path.stem}_p{page_num:03d}"
    subprocess.run(
        [
            pdftoppm,
            "-f",
            str(page_num),
            "-l",
            str(page_num),
            "-singlefile",
            "-png",
            "-r",
            str(dpi),
            str(pdf_path),
            str(prefix),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    image_path = prefix.with_suffix(".png")
    if not image_path.exists():
        raise RuntimeError(f"pdftoppm did not create {image_path}")
    return image_path


def ocr_page(tesseract: str, image_path: Path, languages: str, psm: str) -> str:
    result = subprocess.run(
        [tesseract, str(image_path), "stdout", "-l", languages, "--psm", psm],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return clean_text(result.stdout)


def build_chunks_with_ocr(cps_dir: Path, languages: str, psm: str, dpi: int, force_ocr: bool) -> pd.DataFrame:
    tesseract = find_binary("tesseract")
    pdftoppm = find_binary("pdftoppm", BUNDLED_PDFTOPPM_CANDIDATES)
    missing = []
    if not tesseract:
        missing.append("tesseract")
    if not pdftoppm:
        missing.append("pdftoppm")
    if missing:
        raise SystemExit(
            "Missing OCR dependency: "
            + ", ".join(missing)
            + "\nInstall Tesseract with Korean language data, then rerun:\n"
            + "  brew install tesseract tesseract-lang\n"
            + "or provide an environment where `tesseract --list-langs` includes `kor`."
        )

    rows: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="koda_cps_ocr_") as tmp:
        tmpdir = Path(tmp)
        for pdf_path in sorted(cps_dir.glob("*.pdf")):
            code = pdf_path.stem.upper()
            country = CODE_TO_KR.get(code, code)
            text_layer_pages = extract_page_texts(pdf_path)
            for page_num, text, method in text_layer_pages:
                chosen = text
                extraction_method = method
                if force_ocr or is_noisy(chosen):
                    image_path = render_page(pdftoppm, pdf_path, page_num, tmpdir, dpi)
                    chosen = ocr_page(tesseract, image_path, languages, psm)
                    extraction_method = f"tesseract-ocr:{languages}"
                if is_noisy(chosen):
                    continue
                for idx, chunk in enumerate(chunk_page_text(chosen), start=1):
                    chunk_id = f"CPS-{code}-p{page_num:02d}-{idx:02d}"
                    rows.append(
                        {
                            "Chunk_ID": chunk_id,
                            "Country_KR": country,
                            "Country_Code": code,
                            "PDF_File": pdf_path.name,
                            "Page": page_num,
                            "Chunk_On_Page": idx,
                            "Sector_Tag": sector_tag(chunk),
                            "Text": chunk,
                            "Text_Length": len(chunk),
                            "Extraction_Method": extraction_method,
                            "Citation": f"CPS {country} 국가협력전략 {pdf_path.name} p.{page_num}",
                        }
                    )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build CPS RAG chunks with Tesseract OCR fallback.")
    parser.add_argument("--input", default=str(DEFAULT_CPS_DIR), help="Directory containing CPS PDF files.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output chunk CSV path.")
    parser.add_argument("--languages", default="kor+eng", help="Tesseract languages, e.g. kor+eng.")
    parser.add_argument("--psm", default="6", help="Tesseract page segmentation mode.")
    parser.add_argument("--dpi", default=220, type=int, help="Rasterization DPI for OCR pages.")
    parser.add_argument("--force-ocr", action="store_true", help="OCR every page instead of only noisy/missing text pages.")
    args = parser.parse_args()

    cps_dir = Path(args.input).expanduser()
    if not cps_dir.exists():
        raise FileNotFoundError(cps_dir)

    df = build_chunks_with_ocr(cps_dir, args.languages, args.psm, args.dpi, args.force_ocr)
    if df.empty:
        raise RuntimeError("No CPS chunks were extracted after OCR.")
    output = Path(args.output)
    df.to_csv(output, index=False, encoding="utf-8-sig")
    ocr_rows = int(df["Extraction_Method"].astype(str).str.contains("tesseract-ocr", regex=False).sum())
    print(f"wrote {output.resolve()} rows={len(df)} countries={df['Country_KR'].nunique()} ocr_rows={ocr_rows}")


if __name__ == "__main__":
    main()
