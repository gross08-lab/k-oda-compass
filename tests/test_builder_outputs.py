from __future__ import annotations

import importlib.util
import re
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
    proposal_pdf_markdown = app.build_proposal_pdf_markdown(
        country,
        sector,
        "CSO/NGO",
        "소규모 파일럿",
        "디지털 행정, 현지 역량강화, 성과관리",
        row,
        result,
        "Local RAG",
    )
    proposal_pdf = app.markdown_to_pdf_bytes(
        "K-ODA Compass 근거 기반 AI 사업제안서",
        proposal_pdf_markdown,
    )
    brief_pdf = app.markdown_to_pdf_bytes(
        "K-ODA Compass 1-page Brief",
        brief,
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
        "proposal_pdf_markdown": proposal_pdf_markdown,
        "proposal_pdf": proposal_pdf,
        "brief_pdf": brief_pdf,
    }


def test_repository_korean_fonts_and_license_exist() -> None:
    assert app.REGULAR_FONT_PATH.exists()
    assert app.BOLD_FONT_PATH.exists()
    assert app.FONT_LICENSE_PATH.exists()
    assert "SIL Open Font License, Version 1.1" in app.FONT_LICENSE_PATH.read_text(encoding="utf-8")


def test_direct_evidence_matches_selected_country_and_sector(builder_artifacts: dict) -> None:
    docs = builder_artifacts["docs"]
    direct = docs.loc[docs["Is_Direct_Evidence"]]

    assert not direct.empty
    assert direct["Country_KR"].eq(builder_artifacts["country"]).all()
    assert direct["Sector_Group"].eq(builder_artifacts["sector"]).all()
    assert not ((direct["Source_Type"] == "CPS PDF") & (direct["Sector_Group"] != "공공행정")).any()
    assert not ((direct["Source_Type"] == "Sector Portfolio") & (direct["Sector_Group"] != "공공행정")).any()


def test_public_admin_semantic_relevance_overrides_csv_sector_label(builder_artifacts: dict) -> None:
    docs = builder_artifacts["docs"].set_index("Citation_ID")

    assert docs.loc["E01", "Directness"] == "간접 관련 협력경험"
    assert docs.loc["E02", "Directness"] == "간접 관련 협력경험"
    assert docs.loc["E03", "Directness"] == "직접 유사사업"
    assert bool(docs.loc["E03", "Is_Direct_Evidence"])
    assert docs.loc["E04", "Directness"] == "분야 불일치 · 직접근거 제외"
    assert not bool(docs.loc["E04", "Proposal_Use"])
    assert docs.loc["E05", "Directness"] == "CPS 국가배경 참고근거"
    assert docs.loc["E09", "Directness"] == "공공행정 정책방향 직접근거"
    assert bool(docs.loc["E09", "Is_Direct_Evidence"])
    assert docs.loc["E10", "Directness"] == "분야 의미 관련성 낮음 · Proposal 제외"
    assert not bool(docs.loc["E10", "Proposal_Use"])

    koica_direct = docs.loc[(docs["Source_Type"] == "KOICA Project") & docs["Is_Direct_Evidence"]]
    cps_direct = docs.loc[(docs["Source_Type"] == "CPS PDF") & docs["Is_Direct_Evidence"]]
    assert koica_direct.index.tolist() == ["E03"]
    assert cps_direct.index.tolist() == ["E09"]
    assert docs.loc["E01", "relevance_type"] == "간접 관련 협력경험"
    assert docs.loc["E03", "evidence_role"] == "공공행정 직접 유사사업"
    assert bool(docs.loc["E05", "proposal_used"])
    assert not bool(docs.loc["E04", "proposal_used"])
    assert not bool(docs.loc["E10", "proposal_used"])


def test_proposal_uses_only_semantically_relevant_direct_evidence(builder_artifacts: dict) -> None:
    proposal = builder_artifacts["proposal"]

    assert "[E03] **직접 유사사업**" in proposal
    assert "[E01] **간접 관련 협력경험**" in proposal
    assert "[E02] **간접 관련 협력경험**" in proposal
    assert "[E05] **CPS 국가배경 참고근거**" in proposal
    assert "[E09] **공공행정 정책방향 직접근거**" in proposal
    assert "[E04]" not in proposal
    assert "[E10]" not in proposal


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
    brief_pdf = builder_artifacts["brief_pdf"]

    assert proposal_pdf is not None
    assert proposal_pdf.startswith(b"%PDF")
    assert b"/FontFile2" in proposal_pdf
    assert b"Helvetica" not in proposal_pdf
    assert len(proposal_pdf) > 50_000
    assert len(re.findall(rb"/Type\s*/Page(?!s)", proposal_pdf)) == 2
    assert brief_pdf is not None
    assert brief_pdf.startswith(b"%PDF")
    assert b"/FontFile2" in brief_pdf


def test_proposal_pdf_uses_balanced_two_page_summary(builder_artifacts: dict) -> None:
    pdf_markdown = builder_artifacts["proposal_pdf_markdown"]

    assert pdf_markdown.count("\n---\n") == 1
    assert "####" not in pdf_markdown
    assert "###" not in pdf_markdown
    assert "| 직접 CPS 정책근거 | [E09] |" in pdf_markdown
    assert "| 직접 KOICA 유사사업 | [E03] |" in pdf_markdown
    assert "| 간접 협력경험 | [E01], [E02], [E06], [E07] |" in pdf_markdown
    assert "| 정책·실행환경 파생근거 | [E12] |" in pdf_markdown
    assert "| WDI 보조신호 | [E13], [E14], [E15], [E16] |" in pdf_markdown
    assert "E04" not in pdf_markdown
    assert "E10" not in pdf_markdown
    for assumption_id in (f"A{index:02d}" for index in range(1, 8)):
        assert f"[{assumption_id}]" in pdf_markdown


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


def test_citation_prefix_and_requested_language_are_normalized() -> None:
    source = (
        "KOICA는 관련 정책방향을 제시하며 본 사업을 지원하고자 합니다 [5]. "
        "실행가능성은 시사로 평가됩니다 [E12]."
    )
    normalized = app.normalize_generated_proposal_language(source)

    assert "[E05]" in normalized
    assert "[E12]" in normalized
    assert "[5]" not in normalized
    assert "CPS는 관련 정책방향을 제시하며 본 사업은 정합성을 예비 검토합니다" in normalized
    assert "공개지표는 일정 수준의 실행 가능성을 시사하지만 추가 검증이 필요합니다" in normalized


def test_llm_output_uses_normalized_evidence_for_appendix_and_claims(builder_artifacts: dict) -> None:
    result = builder_artifacts["result"]
    docs = builder_artifacts["docs"]
    appendix = app.structured_result_appendix(result, docs)

    assert "| E01 | Source Evidence | 간접 관련 협력경험 | 한국의 간접 관련 협력경험 |" in appendix
    assert "| E02 | Source Evidence | 간접 관련 협력경험 | 한국의 간접 관련 협력경험 |" in appendix
    assert "| E03 | Source Evidence | 직접 유사사업 | 공공행정 직접 유사사업 |" in appendix
    assert "| E05 | Source Evidence | CPS 국가배경 참고근거 | 탄자니아 ODA·공여 국가배경 참고 |" in appendix
    assert "| E09 | Source Evidence | 공공행정 정책방향 직접근거 | CPS 공공행정 정책방향 직접근거 |" in appendix
    assert "| E04 |" not in appendix
    assert "| E10 |" not in appendix

    llm_text = (
        "정책정합성은 CPS에서 확인된다 [E05], [E09].\n"
        "1인당 GDP가 낮으므로 교육·건강 여건이 낮고 공공행정 현대화가 긴급하다. [E13]\n"
        "기존 KOICA 사업을 통해 효과성을 입증할 수 있다. [E03]\n"
        "농업 인프라 사업도 직접근거다 [E04].\n"
        "## Evidence Class 요약\n"
        "| Evidence ID | Evidence Class |\n|---|---|\n| E04 | Source Evidence |\n"
        "## 다음 섹션\n본문"
    )
    stripped = app.strip_llm_structured_evidence_sections(llm_text)
    normalized = app.normalize_generated_proposal_language(stripped, result)
    policy_line = normalized.splitlines()[0]

    assert "[E09]" in policy_line
    assert "[E05]" not in policy_line
    assert "공공행정 사업의 직접 수요나 긴급성을 단독으로 입증하지 않는다" in normalized
    assert "사업 효과성과 현지 수요는 별도로 검증해야 한다" in normalized
    assert "[E04]" not in normalized
    assert "| E04 |" not in stripped
