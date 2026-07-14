from __future__ import annotations

import argparse
import csv
import hashlib
import re
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
QUERY_VARIANTS = (
    ("direct_keyword", "direct_query"),
    ("semantic_paraphrase", "semantic_query"),
    ("cross_language", "cross_language_query"),
    ("policy_alignment", "policy_query"),
)


def normalize(text: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", str(text).lower())


def split_for(query_id: str) -> str:
    value = int(hashlib.sha256(f"koda-retrieval-v2|{query_id}".encode()).hexdigest()[:8], 16)
    return "dev" if value / 0xFFFFFFFF < 0.30 else "test"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def pdf_page_text(pdf_path: Path, page_number: int) -> str:
    reader = PdfReader(str(pdf_path))
    return reader.pages[page_number - 1].extract_text() or ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the frozen 27-country CPS retrieval Gold Set.")
    parser.add_argument("--pdf-dir", type=Path, default=ROOT / "data" / "cps_pdfs")
    parser.add_argument("--sources", type=Path, default=ROOT / "benchmarks" / "retrieval_gold_sources.csv")
    parser.add_argument("--page-cache", type=Path, default=ROOT / "data" / "cps_page_text.csv")
    args = parser.parse_args()

    chunks = {row["Chunk_ID"]: row for row in read_rows(ROOT / "KODA_cps_pdf_chunks.csv")}
    page_rows = read_rows(args.page_cache)
    pages = {(row["PDF_File"], int(float(row["Page"]))): row for row in page_rows}
    source_cases = read_rows(args.sources)
    gold_rows: list[dict[str, object]] = []
    validation_rows: list[dict[str, object]] = []

    for case in source_cases:
        source = chunks.get(case["chunk_id"])
        if source is None:
            raise RuntimeError(f"Missing Gold source chunk: {case['chunk_id']}")
        pdf_file = source["PDF_File"]
        page_number = int(float(source["Page"]))
        page = pages.get((pdf_file, page_number))
        if page is None:
            raise RuntimeError(f"Missing page cache row: {pdf_file} p.{page_number}")
        pdf_path = args.pdf_dir / pdf_file
        if not pdf_path.exists():
            raise FileNotFoundError(pdf_path)

        source_sha = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
        chunk_norm = normalize(source["Text"])
        page_norm = normalize(page["Text"])
        cache_match = bool(chunk_norm) and chunk_norm in page_norm
        text_layer_match = chunk_norm in normalize(pdf_page_text(pdf_path, page_number))
        is_ocr = "-ocr:" in source["Extraction_Method"]
        hash_match = source.get("Source_SHA256") == source_sha == page.get("Source_SHA256")
        country_match = source["Country_KR"] == case["country"]
        sector_match = source["Sector_Tag"] == case["sector"]
        verified = cache_match and hash_match and country_match and sector_match
        verification_method = (
            "OCR page cache + original PDF SHA-256" if is_ocr
            else "PDF text layer + page cache + original PDF SHA-256"
        )

        for query_type, query_column in QUERY_VARIANTS:
            query_id = f"GOLD-{case['case_id']}-{query_type.upper()}"
            gold_rows.append({
                "query_id": query_id,
                "query_text": case[query_column],
                "query_type": query_type,
                "country": case["country"],
                "sector": case["sector"],
                "expected_chunk_ids": case["chunk_id"],
                "expected_document": pdf_file,
                "expected_pdf_pages": page_number,
                "evidence_class": "Source Evidence",
                "label_source": verification_method,
                "label_verified": str(verified).lower(),
                "split": split_for(query_id),
                "notes": case["review_note"],
            })
            validation_rows.append({
                "query_id": query_id,
                "source_chunk_id": case["chunk_id"],
                "pdf_file": pdf_file,
                "pdf_file_page": page_number,
                "extraction_method": source["Extraction_Method"],
                "normalized_chunk_chars": len(chunk_norm),
                "normalized_page_chars": len(page_norm),
                "chunk_is_page_cache_substring": cache_match,
                "chunk_is_pdf_text_substring": text_layer_match,
                "source_sha256_match": hash_match,
                "country_match": country_match,
                "sector_match": sector_match,
                "label_verified": verified,
            })

        if case.get("negative_type"):
            query_id = f"GOLD-{case['case_id']}-NEGATIVE_{case['negative_type'].upper()}"
            country = case["negative_country"] or case["country"]
            sector = case["negative_sector"] or case["sector"]
            gold_rows.append({
                "query_id": query_id,
                "query_text": case["semantic_query"],
                "query_type": f"negative_{case['negative_type']}",
                "country": country,
                "sector": sector,
                "expected_chunk_ids": "",
                "expected_document": pdf_file,
                "expected_pdf_pages": page_number,
                "evidence_class": "Source Evidence",
                "label_source": verification_method,
                "label_verified": str(verified).lower(),
                "split": split_for(query_id),
                "notes": f"Metadata mismatch negative grounded in {case['chunk_id']}",
            })
            validation_rows.append({
                "query_id": query_id,
                "source_chunk_id": case["chunk_id"],
                "pdf_file": pdf_file,
                "pdf_file_page": page_number,
                "extraction_method": source["Extraction_Method"],
                "normalized_chunk_chars": len(chunk_norm),
                "normalized_page_chars": len(page_norm),
                "chunk_is_page_cache_substring": cache_match,
                "chunk_is_pdf_text_substring": text_layer_match,
                "source_sha256_match": hash_match,
                "country_match": country_match,
                "sector_match": sector_match,
                "label_verified": verified,
            })

    if len(source_cases) != 27 or len(gold_rows) != 120:
        raise RuntimeError(f"Expected 27 source cases and 120 queries, got {len(source_cases)} and {len(gold_rows)}")
    write_rows(ROOT / "benchmarks" / "retrieval_gold_set.csv", gold_rows)
    write_rows(ROOT / "benchmarks" / "retrieval_gold_set_validation.csv", validation_rows)

    verified = sum(str(row["label_verified"]).lower() == "true" for row in gold_rows)
    dev = sum(row["split"] == "dev" for row in gold_rows)
    ocr_cases = sum("-ocr:" in chunks[row["chunk_id"]]["Extraction_Method"] for row in source_cases)
    notes = f"""# Retrieval Gold Set Notes

## Scope

- Internal frozen Gold Set, not external expert validation.
- Source cases: {len(source_cases)} policy pages across 27 CPS countries.
- Query forms: {len(gold_rows)}.
- Verified query labels: {verified}/{len(gold_rows)}.
- Positive queries: {sum(bool(row['expected_chunk_ids']) for row in gold_rows)}.
- Negative metadata queries: {sum(not bool(row['expected_chunk_ids']) for row in gold_rows)}.
- OCR-backed source cases: {ocr_cases}/{len(source_cases)}.
- Frozen dev/test split: {dev}/{len(gold_rows) - dev}.

## Label Construction

- One policy-support page was selected per country before retrieval benchmarking.
- Every source Chunk ID is matched to the page cache, country, sector, original PDF SHA-256 and page number.
- Text-layer cases also require a direct normalized substring match to the original PDF text layer.
- OCR cases retain the original PDF hash, file page, OCR method and page cache because image-only pages have no source text layer.
- Four manually written positive query forms are attached to every source page: direct keyword, semantic paraphrase, cross-language and policy alignment.
- Twelve cases add one deliberately mismatched country or sector query to test metadata controls.
- Retrieval outputs are not used to create or change labels.

## Interpretation Boundary

- The 120 value is the number of frozen query forms, not 120 independently reviewed source pages.
- Semantic relevance remains an internal project review, not an external expert judgment.
- OCR-backed labels require the rendered source page to remain available for human spot-checking.
"""
    (ROOT / "benchmarks" / "retrieval_gold_set_notes.md").write_text(notes, encoding="utf-8")
    print(f"queries={len(gold_rows)} verified={verified} dev={dev} test={len(gold_rows)-dev} ocr_cases={ocr_cases}")


if __name__ == "__main__":
    main()
