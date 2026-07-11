from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
APP_SPEC = importlib.util.spec_from_file_location("koda_builder_app", ROOT / "app.py")
assert APP_SPEC and APP_SPEC.loader
app = importlib.util.module_from_spec(APP_SPEC)
APP_SPEC.loader.exec_module(app)


@pytest.fixture(scope="module")
def builder_artifacts() -> dict:
    data = app.load_all_data()
    country, sector = "탄자니아", "공공행정"
    frames = {
        key: frame.loc[frame["Country_KR"] == country].copy()
        for key, frame in {
            "master": data["master"],
            "wdi": data["wdi"],
            "projects": data["projects"],
            "policy_risk": data["policy_risk"],
            "sector_summary": data["sector_summary"],
            "cps_pdf": data["cps_pdf"],
        }.items()
    }
    corpus = app.build_rag_corpus(
        frames["master"],
        frames["wdi"],
        frames["projects"],
        frames["policy_risk"],
        frames["sector_summary"],
        frames["cps_pdf"],
    )
    row = frames["master"].iloc[0]
    docs = app.retrieve_rag_evidence(
        corpus,
        country,
        sector,
        "디지털 행정, 현지 역량강화, 성과관리",
        row,
        top_k=16,
    )
    assumptions = app.normalize_design_assumptions()
    result = app.build_builder_result(country, sector, docs, assumptions)
    proposal = app.build_rag_markdown_proposal(
        country,
        sector,
        "CSO/NGO",
        "소규모 파일럿",
        "디지털 행정, 현지 역량강화, 성과관리",
        row,
        docs,
        data["weights"],
        assumptions,
        result,
    )
    brief = app.build_policy_brief(country, sector, row, docs, assumptions, result)
    evidence_pack = app.build_rag_evidence_pack(country, sector, "디지털 행정", docs, assumptions, result)
    proposal_pdf = app.markdown_to_pdf_bytes(
        "K-ODA Compass 탄자니아 공공행정 근거 기반 AI 사업제안서",
        proposal,
    )
    return {
        "country": country,
        "sector": sector,
        "corpus": corpus,
        "docs": docs,
        "result": result,
        "proposal": proposal,
        "brief": brief,
        "evidence_pack": evidence_pack,
        "proposal_pdf": proposal_pdf,
    }


def test_repository_korean_fonts_and_license_exist() -> None:
    assert app.REGULAR_FONT_PATH.exists()
    assert app.BOLD_FONT_PATH.exists()
    assert app.FONT_LICENSE_PATH.exists()
    assert "SIL Open Font License, Version 1.1" in app.FONT_LICENSE_PATH.read_text(encoding="utf-8")


def test_direct_evidence_matches_selected_country_and_sector(builder_artifacts: dict) -> None:
    docs = builder_artifacts["docs"]
    direct = docs.loc[docs["Directness"] == "직접근거"]

    assert not direct.empty
    assert direct["Country_KR"].eq(builder_artifacts["country"]).all()
    assert direct["Sector_Group"].eq(builder_artifacts["sector"]).all()
    assert not ((direct["Source_Type"] == "CPS PDF") & (direct["Sector_Group"] != "공공행정")).any()
    assert not ((direct["Source_Type"] == "Sector Portfolio") & (direct["Sector_Group"] != "공공행정")).any()


def test_koica_repeated_project_rows_are_consolidated(builder_artifacts: dict) -> None:
    corpus = builder_artifacts["corpus"]
    digital_records = corpus.loc[
        (corpus["Source_Type"] == "KOICA Project")
        & corpus["Title"].str.contains("Digital Records", case=False, na=False)
    ]

    assert len(digital_records) == 1
    assert int(digital_records.iloc[0]["Record_Count"]) == 2
    assert digital_records.iloc[0]["Observed_Years"] == "2023, 2024"
    assert digital_records.iloc[0]["Project_Period"] == "2023–2025"
    assert "동일 사업 가능성" in digital_records.iloc[0]["Duplicate_Status"]


def test_proposal_separates_sources_assumptions_and_safe_language(builder_artifacts: dict) -> None:
    proposal = builder_artifacts["proposal"]

    for heading in (
        "Source Evidence",
        "Supplementary Source",
        "Derived Evidence",
        "Model Output",
        "AI Design Assumption",
        "국가 개발여건 보조 신호",
    ):
        assert heading in proposal
    for forbidden in (
        "국제기구 연계 권고",
        "국제기구 참여 필요",
        "lower_is_higher_need",
        "higher_is_higher_need",
        "2,021",
        "2,023",
        "2,024",
        "2,025",
    ):
        assert forbidden not in proposal
    assert "잠정 12개월" in proposal
    assert "현지조사 후 확정" in proposal


def test_evidence_pack_has_traceability_metadata(builder_artifacts: dict) -> None:
    evidence_pack = builder_artifacts["evidence_pack"]

    for field in (
        "Evidence Class",
        "제공기관",
        "데이터셋·문서명",
        "수집일",
        "출처 URL",
        "원자료 파일명",
        "원자료 ID",
        "모델에서의 역할",
        "제한사항",
        "AI 생성 예비 설계 가정",
    ):
        assert field in evidence_pack
    assert "수집일 메타데이터 없음" in evidence_pack
    assert "출처 URL 미등록 · 원자료 파일에서 확인" in evidence_pack


def test_pdf_is_generated_with_embedded_truetype_font(builder_artifacts: dict) -> None:
    proposal_pdf = builder_artifacts["proposal_pdf"]

    assert proposal_pdf is not None
    assert proposal_pdf.startswith(b"%PDF")
    assert b"/FontFile2" in proposal_pdf
    assert b"Helvetica" not in proposal_pdf
    assert len(proposal_pdf) > 50_000


def test_builder_quality_report_has_no_block(builder_artifacts: dict) -> None:
    status, report = app.builder_output_quality_report(
        builder_artifacts["country"],
        builder_artifacts["sector"],
        builder_artifacts["docs"],
        builder_artifacts["proposal"],
        builder_artifacts["brief"],
        builder_artifacts["evidence_pack"],
        builder_artifacts["proposal_pdf"],
        builder_artifacts["result"],
    )

    assert status == "REVIEW"
    assert not report["상태"].eq("BLOCK").any()
    assert report.loc[report["검사 항목"] == "Citation ID 무결성", "상태"].iloc[0] == "PASS"
    for item in ("AI 설계 가정", "원천·파생근거 구분", "WDI 역할", "Citation 의미 정합성"):
        assert report.loc[report["검사 항목"] == item, "상태"].iloc[0] == "PASS"


def test_structured_result_is_shared_by_all_outputs(builder_artifacts: dict) -> None:
    result = builder_artifacts["result"]
    assumptions = result["assumptions"]
    evidence = result["evidence"]

    assert [item["assumption_id"] for item in assumptions] == [f"A{index:02d}" for index in range(1, 8)]
    assert all(item["evidence_class"] == "AI Design Assumption" for item in assumptions)
    assert all(item.get("Evidence_Class") for item in evidence)
    for output_name in ("proposal", "brief", "evidence_pack"):
        output = builder_artifacts[output_name]
        assert "Evidence Class" in output
        assert "AI 생성 예비 설계 가정" in output
        assert "국가 개발여건 보조 신호" in output


def test_citation_semantics_rejects_non_cps_id_for_cps_claim(builder_artifacts: dict) -> None:
    docs = builder_artifacts["docs"]
    non_cps_id = docs.loc[docs["Source_Type"] == "Sector Portfolio", "Citation_ID"].iloc[0]
    mismatches = app.citation_semantic_mismatches(
        f"CPS에서 공공행정 강화를 명시한다([{non_cps_id}]).",
        docs,
    )

    assert len(mismatches) == 1
    assert mismatches[0]["claim_type"] == "CPS 정책 주장"
    assert mismatches[0]["citation_ids"] == non_cps_id
