from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


CSV_FILES = [
    "KODA_master_score_top50_v21.csv",
    "KODA_project_evidence_top50_2019_2024.csv",
    "KODA_wdi_latest_top50_long_v2.csv",
    "KODA_policy_risk_scores_top50_v21.csv",
    "KODA_country_sector_summary_2019_2024.csv",
    "KODA_cps_pdf_chunks.csv",
]


def test_core_csv_files_exist_and_have_no_duplicate_rows() -> None:
    for file_name in CSV_FILES:
        path = ROOT / file_name
        assert path.exists(), file_name
        df = pd.read_csv(path)
        assert not df.empty, file_name
        assert df.duplicated().sum() == 0, file_name


def test_country_coverage_matches_top50() -> None:
    master = pd.read_csv(ROOT / "KODA_master_score_top50_v21.csv")
    countries = set(master["Country_KR"])
    projects = pd.read_csv(ROOT / "KODA_project_evidence_top50_2019_2024.csv")
    wdi = pd.read_csv(ROOT / "KODA_wdi_latest_top50_long_v2.csv")
    policy = pd.read_csv(ROOT / "KODA_policy_risk_scores_top50_v21.csv")

    assert countries == set(projects["Country_KR"])
    assert countries == set(wdi["Country_KR"])
    assert countries == set(policy["Country_KR"])


def test_cps_pdf_chunks_are_usable_for_rag() -> None:
    master = pd.read_csv(ROOT / "KODA_master_score_top50_v21.csv")
    cps = pd.read_csv(ROOT / "KODA_cps_pdf_chunks.csv")
    assert cps["Chunk_ID"].is_unique
    assert cps["Text_Length"].min() >= 120
    assert cps["Country_KR"].nunique() >= 20
    assert len(set(master["WDI_Country_Code"]) & set(cps["Country_Code"])) >= 19
