from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from scripts.verify_retrieval_gold_freeze import verify as verify_gold_freeze


ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_frozen_gold_hash_split_and_labels() -> None:
    result = verify_gold_freeze(ROOT)
    assert result["status"] == "PASS"
    assert result["gold_rows"] == 120
    assert result["dev_rows"] == 29
    assert result["test_rows"] == 91
    assert result["gold_label_fingerprint"] == "c42d43130647b074d5c8e6b7b856aef44009a549f768f17433506792821d0446"


def test_cps_pdf_page_cache_and_chunk_inventory() -> None:
    pdfs = sorted((ROOT / "data" / "cps_pdfs").glob("*.pdf"))
    manifest = pd.read_csv(ROOT / "data" / "cps_document_manifest.csv")
    pages = pd.read_csv(ROOT / "data" / "cps_page_text.csv")
    chunks = pd.read_csv(ROOT / "KODA_cps_pdf_chunks.csv")

    assert len(pdfs) == 27
    assert manifest["Country_Code"].nunique() == 27
    assert int(manifest["Pages"].sum()) == 921
    assert len(pages) == 901
    assert (~pages["Extraction_Method"].astype(str).str.contains("-ocr:", regex=False)).sum() == 652
    assert pages["Extraction_Method"].astype(str).str.contains("-ocr:", regex=False).sum() == 249
    assert len(chunks) == 1100
    assert chunks["Chunk_ID"].is_unique
    assert chunks["Text"].fillna("").str.strip().ne("").all()
    assert chunks["Valid_Chunk"].astype(str).str.lower().eq("true").all()
    assert set(zip(chunks["PDF_File"], chunks["Page"].astype(int))) <= set(
        zip(pages["PDF_File"], pages["Page"].astype(int))
    )


def test_cps_manifest_and_embedding_index_hashes_match() -> None:
    manifest = pd.read_csv(ROOT / "data" / "cps_document_manifest.csv")
    for row in manifest.itertuples(index=False):
        assert sha256_file(ROOT / "data" / "cps_pdfs" / row.PDF_File) == row.SHA256
    index_meta = json.loads(
        (ROOT / "artifacts" / "ai_upgrade" / "embedding_index_metadata.json").read_text(encoding="utf-8")
    )
    assert index_meta["source_sha256"] == sha256_file(ROOT / "KODA_cps_pdf_chunks.csv")
    assert index_meta["valid_rows"] == 1100


def test_validation_artifacts_report_actual_bounded_scope() -> None:
    cps = json.loads(
        (ROOT / "artifacts" / "ai_upgrade" / "cps_corpus_validation.json").read_text(encoding="utf-8")
    )["summary"]
    citation = json.loads(
        (ROOT / "artifacts" / "ai_upgrade" / "citation_audit_summary.json").read_text(encoding="utf-8")
    )
    experiment = json.loads(
        (ROOT / "artifacts" / "ai_upgrade" / "controlled_experiment_summary.json").read_text(encoding="utf-8")
    )
    assert cps["status"] == "PASS"
    assert cps["valid_chunks"] == 1100
    assert citation["citation_occurrences"] == citation["citation_occurrences_resolved"] == 47
    assert citation["claim_citation_human_judgments"] == 0
    assert citation["cohens_kappa"] is None
    if experiment["executed_calls"] == 0:
        assert experiment["status"] == "NOT_EXECUTED_NO_API_KEY"
        assert experiment["claim_allowed"] is False
