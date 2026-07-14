from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
APP_SPEC = importlib.util.spec_from_file_location("koda_screening_app", ROOT / "app.py")
assert APP_SPEC and APP_SPEC.loader
app = importlib.util.module_from_spec(APP_SPEC)
APP_SPEC.loader.exec_module(app)
MANIFEST_PATH = ROOT / "artifacts" / "screening" / "canonical_public_kpis.json"
PUBLIC_SURFACES = [
    ROOT / "README.md",
    ROOT / "app.py",
    *sorted((ROOT / "docs").glob("*.md")),
    MANIFEST_PATH,
]


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_canonical_manifest_matches_reproducible_sources() -> None:
    manifest = load_manifest()
    cps = json.loads((ROOT / manifest["cps"]["source"]).read_text(encoding="utf-8"))["summary"]
    benchmark = json.loads((ROOT / manifest["retrieval"]["source"]).read_text(encoding="utf-8"))
    scores = pd.read_csv(ROOT / manifest["score_reproduction"]["source"])

    assert manifest["cps"]["pdfs"] == cps["pdfs"] == 27
    assert manifest["cps"]["searchable_countries"] == cps["countries"] == 27
    assert manifest["cps"]["total_pages"] == cps["total_pages"] == 921
    assert manifest["cps"]["searchable_pages"] == cps["searchable_pages"] == 901
    assert manifest["cps"]["valid_chunks"] == cps["valid_chunks"] == 1100
    assert manifest["retrieval"]["gold_queries"] == benchmark["gold_queries_verified"] == 120
    assert manifest["retrieval"]["recall_at_5"] == benchmark["operating_mode_test_result"]["Recall@5"] == 1.0
    assert manifest["score_reproduction"]["countries"] == len(scores) == 50
    assert int(scores["Absolute_Error"].le(0.01).sum()) == manifest["score_reproduction"]["score_pass"] == 50
    assert int(scores["Rank_Match"].sum()) == manifest["score_reproduction"]["rank_match"] == 50
    assert scores["Absolute_Error"].max() <= manifest["score_reproduction"]["max_absolute_error"]


def test_app_and_readme_use_the_canonical_public_scope() -> None:
    manifest = load_manifest()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    source = (ROOT / "app.py").read_text(encoding="utf-8")

    assert app.load_public_kpis() == manifest
    assert "canonical_public_kpis.json" in readme
    assert "canonical_public_kpis.json" in source
    assert "manifest만 공개 기준" in readme
    assert f"{manifest['cps']['searchable_pages']}/{manifest['cps']['total_pages']}페이지" not in readme
    assert f"Recall@5 {manifest['retrieval']['recall_at_5']:.3f}" not in readme
    assert f"{manifest['score_reproduction']['score_pass']}/{manifest['score_reproduction']['countries']}개국" not in readme


def test_public_surfaces_do_not_mix_conflicting_diagnostic_values() -> None:
    public_text = "\n".join(path.read_text(encoding="utf-8") for path in PUBLIC_SURFACES)
    forbidden_strings = [
        "0.716",
        "47/47",
        "6 PARTIAL",
        "1 UNRESOLVED",
        "0/30",
    ]
    for forbidden in forbidden_strings:
        assert forbidden not in public_text, forbidden


def test_overview_renders_public_kpis_and_representative_demo_without_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    test_app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=45)
    test_app.session_state["active_view"] = "개요"
    test_app.run()

    rendered = "\n".join(element.value for element in test_app.markdown)
    assert not test_app.exception
    assert "CPS 검색 범위" in rendered
    assert "1,100" in rendered
    assert "120 · 1.000" in rendered
    assert "50/50 PASS" in rendered
    assert any(button.label == "대표 시나리오 열기" for button in test_app.button)


def test_representative_demo_navigation_preserves_country_sector_and_user(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    test_app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    test_app.session_state["active_view"] = "개요"
    test_app.run()

    demo_button = next(button for button in test_app.button if button.label == "대표 시나리오 열기")
    demo_button.click().run()

    demo = load_manifest()["representative_demo"]
    assert not test_app.exception
    assert test_app.session_state["active_view"] == "AI Builder"
    assert test_app.session_state["builder_country"] == demo["country"]
    assert test_app.session_state["builder_sector"] == demo["sector"]
    assert test_app.session_state["builder_user_type"] == demo["user_type"]


def test_all_27_cps_countries_and_ocr_countries_are_searchable() -> None:
    coverage = pd.read_csv(ROOT / "KODA_cps_pdf_ocr_coverage.csv")
    chunks = pd.read_csv(ROOT / "KODA_cps_pdf_chunks.csv")
    searchable_codes = set(chunks.loc[chunks["Text"].fillna("").str.strip().ne(""), "Country_Code"])
    ocr_codes = set(coverage.loc[coverage["OCR_Completed_Pages"] > 0, "Country_Code"])

    assert coverage["Country_Code"].nunique() == 27
    assert coverage["Search_Status"].eq("Searchable").all()
    assert set(coverage["Country_Code"]) == searchable_codes
    assert ocr_codes
    assert ocr_codes <= searchable_codes


def test_cps_citations_have_existing_documents_pages_and_stable_ids() -> None:
    manifest = pd.read_csv(ROOT / "data" / "cps_document_manifest.csv").set_index("PDF_File")
    chunks = pd.read_csv(ROOT / "KODA_cps_pdf_chunks.csv")

    assert chunks["Chunk_ID"].is_unique
    assert chunks["Chunk_ID"].str.fullmatch(r"CPS-[A-Z]{3}-p\d{2}-\d{2}").all()
    assert chunks["Citation"].str.contains(r"[.]pdf p[.]\d+$", regex=True).all()
    for pdf_file, group in chunks.groupby("PDF_File"):
        assert (ROOT / "data" / "cps_pdfs" / pdf_file).exists()
        assert group["Page"].between(1, int(manifest.loc[pdf_file, "Pages"])).all()


def test_public_feature_manifest_covers_evidence_assumptions_and_downloads() -> None:
    features = load_manifest()["features"]
    assert features["evidence_ids"] is True
    assert features["cps_document_and_page_citation"] is True
    assert features["evidence_pack"] is True
    assert features["assumption_ids_a01_a07"] is True
    assert features["local_rag_without_api_key"] is True
    assert features["output_types"] == [
        "Proposal Markdown",
        "Brief Markdown",
        "Evidence Pack Markdown",
        "Proposal PDF",
        "Brief PDF",
    ]


def test_live_and_github_qr_payloads_are_exact_public_urls() -> None:
    manifest = load_manifest()
    access = json.loads((ROOT / "artifacts" / "screening" / "live_access_check.json").read_text(encoding="utf-8"))
    live_url = manifest["urls"]["live_demo"]
    github_url = manifest["urls"]["github"]

    assert app.LIVE_DEMO_URL == access["submitted_pdf_qr"]["live_payload"] == live_url
    assert app.GITHUB_URL == access["submitted_pdf_qr"]["github_payload"] == github_url
    live_qr = app.make_qr_png(live_url)
    github_qr = app.make_qr_png(github_url)
    assert live_qr and live_qr.startswith(b"\x89PNG\r\n\x1a\n")
    assert github_qr and github_qr.startswith(b"\x89PNG\r\n\x1a\n")
    assert hashlib.sha256(live_qr).digest() != hashlib.sha256(github_qr).digest()


def test_internal_claim_matrix_is_not_part_of_the_public_repository_surface() -> None:
    assert not (ROOT / "artifacts" / "screening" / "claim_contradiction_matrix.csv").exists()


def test_public_surfaces_have_no_local_path_secret_or_unimplemented_marker() -> None:
    public_text = "\n".join(path.read_text(encoding="utf-8") for path in PUBLIC_SURFACES)
    assert "/Users/" not in public_text
    assert not re.search(r"sk-[A-Za-z0-9_-]{12,}", public_text)
    assert "<your-id>" not in public_text
    assert "<your-app>" not in public_text
    assert not re.search(r"\b(?:TODO|FIXME|mock|sample only|not implemented)\b", public_text, re.IGNORECASE)


def test_manifest_provenance_and_public_internal_links_exist() -> None:
    manifest = load_manifest()
    sources = {
        manifest["cps"]["source"],
        manifest["retrieval"]["source"],
        manifest["score_reproduction"]["source"],
        "artifacts/ai_upgrade/retrieval_gold_freeze.json",
        "tests/test_app_runtime_smoke.py",
        "tests/test_builder_outputs.py",
    }
    missing = sorted(source for source in sources if not (ROOT / source).exists())
    assert missing == []
