from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
APP_SPEC = importlib.util.spec_from_file_location("koda_app", ROOT / "app.py")
assert APP_SPEC and APP_SPEC.loader
app = importlib.util.module_from_spec(APP_SPEC)
APP_SPEC.loader.exec_module(app)


def load_score_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    master = pd.read_csv(ROOT / "KODA_master_score_top50_v21.csv")
    weights = pd.read_csv(ROOT / "KODA_v21_score_weights.csv")
    return master, weights


def test_internal_score_reproducibility() -> None:
    master, weights = load_score_data()
    result = app.score_model_reproducibility(master, weights)

    assert result["country_count"] == 50
    assert result["pass_count"] == 50
    assert result["max_abs_error"] <= 0.01
    assert result["rank_match_count"] == 50
    assert result["rank_all_match"] is True


def test_sensitivity_experiment_is_fully_specified() -> None:
    master, weights = load_score_data()
    result = app.sensitivity_analysis_table(master, weights, delta=0.03)

    assert len(result) == 3
    assert set(result["변경 폭"]) == {"+3%p"}
    assert result["나머지 재정규화"].str.contains("총합 1.0000", regex=False).all()
    assert result["최대 순위 변화"].max() == 6
    assert result["Top10 중첩"].isin({"8/10", "9/10", "10/10"}).all()
    assert result["순위상관"].between(0, 1).all()


def test_citation_integrity_detects_unknown_duplicate_and_unused_ids() -> None:
    docs = pd.DataFrame({"Citation_ID": ["E01", "E02"]})
    result = app.citation_integrity_metrics("근거 [E01], 재인용 [E01], 오류 [E99]", docs)

    assert result["citation_count"] == 3
    assert result["resolved_count"] == 2
    assert result["unknown_ids"] == ["E99"]
    assert result["duplicate_count"] == 1
    assert result["unused_evidence_ids"] == ["E02"]


def test_fallback_branches_do_not_claim_unrun_external_api_success() -> None:
    result = app.fallback_self_test_results()

    assert result["상태"].eq("PASS").sum() == 5
    assert result["상태"].eq("INFO").sum() == 1
    assert not result["상태"].eq("FAIL").any()
    assert result.loc[result["검증 항목"] == "민감정보 로그", "상태"].iloc[0] == "INFO"
