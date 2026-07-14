from __future__ import annotations

import argparse
import hashlib
import os
import platform
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


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAGE_CACHE = ROOT / "data" / "cps_page_text.csv"
VISION_SOURCE = Path(__file__).with_name("vision_ocr.m")


def find_binary(name: str, fallbacks: list[Path] | None = None) -> str | None:
    configured = os.getenv(name.upper())
    if configured and Path(configured).exists():
        return configured
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


def compile_vision_ocr(tmpdir: Path) -> str:
    xcrun = find_binary("xcrun")
    if platform.system() != "Darwin" or not xcrun or not VISION_SOURCE.exists():
        raise RuntimeError("macOS Vision OCR compiler is unavailable")
    binary = tmpdir / "vision_ocr"
    module_cache = tmpdir / "clang-module-cache"
    module_cache.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["CLANG_MODULE_CACHE_PATH"] = str(module_cache)
    subprocess.run(
        [
            xcrun,
            "clang",
            "-fobjc-arc",
            "-fblocks",
            str(VISION_SOURCE),
            "-framework",
            "Foundation",
            "-framework",
            "AppKit",
            "-framework",
            "Vision",
            "-o",
            str(binary),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    return str(binary)


def resolve_ocr_backend(engine: str, tmpdir: Path) -> tuple[str, str]:
    tesseract = find_binary("tesseract")
    if engine == "tesseract":
        if not tesseract:
            raise RuntimeError("Tesseract OCR is unavailable")
        return "tesseract", tesseract
    if engine == "vision":
        return "vision", compile_vision_ocr(tmpdir)
    if tesseract:
        return "tesseract", tesseract
    return "vision", compile_vision_ocr(tmpdir)


def ocr_page(
    backend: str,
    binary: str,
    image_path: Path,
    languages: str,
    vision_languages: str,
    psm: str,
) -> str:
    if backend == "tesseract":
        command = [binary, str(image_path), "stdout", "-l", languages, "--psm", psm]
    else:
        selected_languages = [value.strip() for value in vision_languages.split(",") if value.strip()]
        command = [binary, str(image_path), *selected_languages]
    result = subprocess.run(
        command,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return clean_text(result.stdout)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def extract_searchable_pages(
    cps_dir: Path,
    engine: str,
    languages: str,
    vision_languages: str,
    psm: str,
    dpi: int,
    force_ocr: bool,
) -> pd.DataFrame:
    pdftoppm = find_binary("pdftoppm")
    if not pdftoppm:
        raise SystemExit("Missing OCR dependency: pdftoppm. Set PDFTOPPM or install Poppler.")

    pages: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="koda_cps_ocr_") as tmp:
        tmpdir = Path(tmp)
        backend, ocr_binary = resolve_ocr_backend(engine, tmpdir)
        print(f"OCR backend={backend}", flush=True)
        for pdf_path in sorted(cps_dir.glob("*.pdf")):
            code = pdf_path.stem.upper()
            country = CODE_TO_KR.get(code, code)
            text_layer_pages = extract_page_texts(pdf_path)
            source_sha256 = sha256_file(pdf_path)
            file_pages_before = len(pages)
            for page_num, text, method in text_layer_pages:
                chosen = text
                extraction_method = method
                if force_ocr or is_noisy(chosen):
                    image_path = render_page(pdftoppm, pdf_path, page_num, tmpdir, dpi)
                    chosen = ocr_page(
                        backend,
                        ocr_binary,
                        image_path,
                        languages,
                        vision_languages,
                        psm,
                    )
                    language_label = languages if backend == "tesseract" else vision_languages.replace(",", "+")
                    extraction_method = f"{backend}-ocr:{language_label}"
                if is_noisy(chosen):
                    continue
                pages.append({
                    "Country_KR": country,
                    "Country_Code": code,
                    "PDF_File": pdf_path.name,
                    "Source_SHA256": source_sha256,
                    "Page": page_num,
                    "Text": chosen,
                    "Text_Length": len(chosen),
                    "Extraction_Method": extraction_method,
                })
            print(
                f"processed {pdf_path.name} pages={len(text_layer_pages)} searchable={len(pages) - file_pages_before}",
                flush=True,
            )
    return pd.DataFrame(pages)


def validate_page_cache(page_frame: pd.DataFrame, cps_dir: Path) -> None:
    required = {"Country_KR", "Country_Code", "PDF_File", "Source_SHA256", "Page", "Text", "Extraction_Method"}
    missing = sorted(required - set(page_frame.columns))
    if missing:
        raise RuntimeError(f"Page cache is missing columns: {', '.join(missing)}")
    source_files = sorted(cps_dir.glob("*.pdf"))
    if {path.name for path in source_files} != set(page_frame["PDF_File"].astype(str)):
        raise RuntimeError("Page cache PDF inventory does not match the input directory")
    cached_hashes = page_frame.groupby("PDF_File")["Source_SHA256"].first().to_dict()
    stale = [path.name for path in source_files if cached_hashes.get(path.name) != sha256_file(path)]
    if stale:
        raise RuntimeError(f"Page cache is stale for: {', '.join(stale)}")


def build_chunks_from_pages(page_frame: pd.DataFrame, max_chars: int, overlap: int) -> pd.DataFrame:
    rows: list[dict] = []
    for page in page_frame.sort_values(["Country_Code", "Page"]).to_dict(orient="records"):
        text = clean_text(str(page["Text"]))
        for index, chunk in enumerate(chunk_page_text(text, max_chars=max_chars, overlap=overlap), start=1):
            content_sha256 = hashlib.sha256(chunk.encode("utf-8")).hexdigest()
            rows.append({
                "Chunk_ID": f"CPS-{page['Country_Code']}-p{int(page['Page']):02d}-{index:02d}",
                "Country_KR": page["Country_KR"],
                "Country_Code": page["Country_Code"],
                "PDF_File": page["PDF_File"],
                "Page": int(page["Page"]),
                "Chunk_On_Page": index,
                "Sector_Tag": sector_tag(chunk),
                "Text": chunk,
                "Text_Length": len(chunk),
                "Extraction_Method": page["Extraction_Method"],
                "Source_SHA256": page["Source_SHA256"],
                "Content_SHA256": content_sha256,
                "Citation": f"CPS {page['Country_KR']} 국가협력전략 {page['PDF_File']} p.{int(page['Page'])}",
            })
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    duplicate_counts = frame.groupby("Content_SHA256")["Chunk_ID"].transform("size")
    frame["Duplicate_Text_Count"] = duplicate_counts.astype(int)
    frame["Valid_Chunk"] = frame["Text"].astype(str).str.strip().ne("") & ~frame["Chunk_ID"].duplicated()
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description="Build CPS RAG chunks with Tesseract OCR fallback.")
    parser.add_argument("--input", default=str(DEFAULT_CPS_DIR), help="Directory containing CPS PDF files.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output chunk CSV path.")
    parser.add_argument("--page-cache", default=str(DEFAULT_PAGE_CACHE), help="Reusable page-level extraction CSV.")
    parser.add_argument("--reuse-page-cache", action="store_true", help="Skip OCR and rebuild chunks from a verified cache.")
    parser.add_argument("--engine", choices=("auto", "tesseract", "vision"), default="auto")
    parser.add_argument("--languages", default="kor+eng", help="Tesseract languages, e.g. kor+eng.")
    parser.add_argument("--vision-languages", default="ko-KR,en-US", help="Comma-separated Vision OCR languages.")
    parser.add_argument("--psm", default="6", help="Tesseract page segmentation mode.")
    parser.add_argument("--dpi", default=220, type=int, help="Rasterization DPI for OCR pages.")
    parser.add_argument("--max-chars", default=1024, type=int, help="Maximum target characters per chunk.")
    parser.add_argument("--overlap", default=120, type=int, help="Character overlap between adjacent chunks.")
    parser.add_argument("--force-ocr", action="store_true", help="OCR every page instead of only noisy/missing text pages.")
    args = parser.parse_args()

    cps_dir = Path(args.input).expanduser()
    if not cps_dir.exists():
        raise FileNotFoundError(cps_dir)

    page_cache = Path(args.page_cache)
    if args.reuse_page_cache:
        page_frame = pd.read_csv(page_cache)
        validate_page_cache(page_frame, cps_dir)
        print(f"reused page cache={page_cache} rows={len(page_frame)}", flush=True)
    else:
        page_frame = extract_searchable_pages(
            cps_dir,
            args.engine,
            args.languages,
            args.vision_languages,
            args.psm,
            args.dpi,
            args.force_ocr,
        )
        page_cache.parent.mkdir(parents=True, exist_ok=True)
        page_frame.to_csv(page_cache, index=False, encoding="utf-8-sig")
        print(f"wrote page cache={page_cache} rows={len(page_frame)}", flush=True)
    df = build_chunks_from_pages(page_frame, args.max_chars, args.overlap)
    if df.empty:
        raise RuntimeError("No CPS chunks were extracted after OCR.")
    output = Path(args.output)
    df.to_csv(output, index=False, encoding="utf-8-sig")
    ocr_rows = int(df["Extraction_Method"].astype(str).str.contains("-ocr:", regex=False).sum())
    print(f"wrote {output.resolve()} rows={len(df)} countries={df['Country_KR'].nunique()} ocr_rows={ocr_rows}")


if __name__ == "__main__":
    main()
