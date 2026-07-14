from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ocr_cps_pdfs import build_chunks_from_pages, sha256_file  # noqa: E402


def frame_sha256(frame: pd.DataFrame) -> str:
    payload = frame.fillna("").to_csv(index=False, lineterminator="\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def check(name: str, observed: Any, expected: Any, detail: str) -> dict[str, Any]:
    serialized_observed = sorted(observed) if isinstance(observed, set) else observed
    serialized_expected = sorted(expected) if isinstance(expected, set) else expected
    return {
        "check_id": name,
        "status": "PASS" if observed == expected else "FAIL",
        "observed": serialized_observed,
        "expected": serialized_expected,
        "detail": detail,
    }


def validate(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    pdf_dir = root / "data" / "cps_pdfs"
    manifest_path = root / "data" / "cps_document_manifest.csv"
    coverage_path = root / "KODA_cps_pdf_ocr_coverage.csv"
    page_cache_path = root / "data" / "cps_page_text.csv"
    chunk_path = root / "KODA_cps_pdf_chunks.csv"

    pdfs = sorted(pdf_dir.glob("*.pdf"))
    manifest = pd.read_csv(manifest_path, dtype={"Country_Code": str})
    coverage = pd.read_csv(coverage_path, dtype={"Country_Code": str})
    pages = pd.read_csv(page_cache_path, dtype={"Country_Code": str})
    chunks = pd.read_csv(chunk_path, dtype={"Country_Code": str})
    rebuilt = build_chunks_from_pages(pages, max_chars=1024, overlap=120)

    manifest_hashes = manifest.set_index("PDF_File")["SHA256"].astype(str).to_dict()
    actual_hashes = {path.name: sha256_file(path) for path in pdfs}
    page_limits = manifest.set_index("PDF_File")["Pages"].astype(int).to_dict()
    cache_keys = set(zip(pages["PDF_File"].astype(str), pages["Page"].astype(int)))
    chunk_keys = set(zip(chunks["PDF_File"].astype(str), chunks["Page"].astype(int)))

    chunk_valid = chunks["Valid_Chunk"].astype(str).str.lower().eq("true")
    empty_text = chunks["Text"].fillna("").astype(str).str.strip().eq("")
    page_out_of_range = chunks.apply(
        lambda row: int(row["Page"]) < 1
        or int(row["Page"]) > int(page_limits.get(str(row["PDF_File"]), 0)),
        axis=1,
    )
    source_hash_mismatch = chunks.apply(
        lambda row: str(row["Source_SHA256"])
        != str(actual_hashes.get(str(row["PDF_File"]), "")),
        axis=1,
    )
    country_pdf_pairs = manifest[["Country_Code", "PDF_File"]].drop_duplicates()
    countries_with_chunks = set(chunks.loc[chunk_valid, "Country_Code"].astype(str))
    manifest_countries = set(manifest["Country_Code"].astype(str))

    checks = [
        check("pdf_inventory", len(pdfs), 27, "Repository CPS PDF files"),
        check("manifest_rows", len(manifest), 27, "One manifest row per PDF"),
        check("unique_country_codes", manifest["Country_Code"].nunique(), 27, "No duplicate country code"),
        check("unique_pdf_country_pairs", len(country_pdf_pairs), 27, "One country mapping per PDF"),
        check("pdf_sha256", actual_hashes, manifest_hashes, "Manifest hashes match source PDFs"),
        check("all_countries_searchable", countries_with_chunks, manifest_countries, "Every CPS country has a valid chunk"),
        check("total_pdf_pages", int(manifest["Pages"].sum()), 921, "Physical PDF pages"),
        check("direct_extracted_pages", int(manifest["Text_Layer_Pages"].sum()), 652, "Non-OCR pages in the final page cache"),
        check("ocr_searchable_pages", int(manifest["OCR_Completed_Pages"].sum()), 249, "OCR-backed pages present in chunks"),
        check("searchable_pages", int(manifest["Searchable_Pages"].sum()), 901, "Unique pages represented by chunks"),
        check("chunk_rows", len(chunks), 1100, "All generated chunk rows"),
        check("valid_chunks", int(chunk_valid.sum()), 1100, "Rows marked valid"),
        check("empty_chunk_text", int(empty_text.sum()), 0, "Blank chunk text"),
        check("duplicate_chunk_ids", int(chunks["Chunk_ID"].duplicated().sum()), 0, "Duplicate stable IDs"),
        check("page_out_of_range", int(page_out_of_range.sum()), 0, "Chunk page within source PDF"),
        check("missing_cache_page", len(chunk_keys - cache_keys), 0, "Every chunk maps to the page cache"),
        check("source_hash_mismatch", int(source_hash_mismatch.sum()), 0, "Chunk-to-PDF hash linkage"),
        check("rebuilt_row_count", len(rebuilt), len(chunks), "Rebuild uses frozen 1024/120 chunking"),
        check("rebuilt_frame_sha256", frame_sha256(rebuilt), frame_sha256(chunks), "Same cache reproduces identical ordered chunk content"),
    ]
    failures = [row for row in checks if row["status"] != "PASS"]
    summary = {
        "validation_date": date.today().isoformat(),
        "status": "PASS" if not failures else "FAIL",
        "pdfs": len(pdfs),
        "countries": len(manifest_countries),
        "total_pages": int(manifest["Pages"].sum()),
        "text_layer_pages": int(manifest["Text_Layer_Pages"].sum()),
        "ocr_searchable_pages": int(manifest["OCR_Completed_Pages"].sum()),
        "searchable_pages": int(manifest["Searchable_Pages"].sum()),
        "valid_chunks": int(chunk_valid.sum()),
        "chunk_file_sha256": sha256_file(chunk_path),
        "page_cache_sha256": sha256_file(page_cache_path),
        "deterministic_chunk_frame_sha256": frame_sha256(chunks),
        "duplicate_content_groups": int(
            (chunks.groupby("Content_SHA256")["Chunk_ID"].size() > 1).sum()
        ),
        "failed_checks": [row["check_id"] for row in failures],
        "source_files": {
            "pdf_manifest": "data/cps_document_manifest.csv",
            "coverage": "KODA_cps_pdf_ocr_coverage.csv",
            "page_cache": "data/cps_page_text.csv",
            "chunks": "KODA_cps_pdf_chunks.csv",
        },
    }
    return summary, checks


def write_outputs(root: Path, summary: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    artifact_dir = root / "artifacts" / "ai_upgrade"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "cps_corpus_validation.json").write_text(
        json.dumps({"summary": summary, "checks": checks}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    with (artifact_dir / "cps_corpus_validation.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(checks[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(checks)
    lines = [
        "# CPS Corpus Validation",
        "",
        f"- Status: **{summary['status']}**",
        f"- Source PDFs / countries: {summary['pdfs']}/{summary['countries']}",
        f"- Pages: {summary['total_pages']} total · {summary['text_layer_pages']} text layer · {summary['ocr_searchable_pages']} OCR searchable · {summary['searchable_pages']} total searchable",
        f"- Valid chunks: {summary['valid_chunks']}",
        f"- Chunk SHA-256: `{summary['chunk_file_sha256']}`",
        f"- Deterministic frame SHA-256: `{summary['deterministic_chunk_frame_sha256']}`",
        "",
        "| Check | Status | Observed | Expected |",
        "|---|---|---|---|",
    ]
    for row in checks:
        observed = str(row["observed"])
        expected = str(row["expected"])
        if len(observed) > 80:
            observed = "see JSON artifact"
        if len(expected) > 80:
            expected = "see JSON artifact"
        lines.append(f"| {row['check_id']} | {row['status']} | {observed} | {expected} |")
    (artifact_dir / "cps_corpus_validation.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the complete CPS PDF-to-RAG lineage.")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    summary, checks = validate(args.root.resolve())
    write_outputs(args.root.resolve(), summary, checks)
    print(json.dumps(summary, ensure_ascii=False))
    if summary["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
