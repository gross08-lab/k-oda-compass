from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def test_score_formula_reproduces_master_scores() -> None:
    master = pd.read_csv(ROOT / "KODA_master_score_top50_v21.csv")
    weights = pd.read_csv(ROOT / "KODA_v21_score_weights.csv")
    columns = {
        "Development Need": "Development_Need_Score",
        "Korea Cooperation Base": "Korea_Coop_Base_Score_V2",
        "Sector Fit": "Sector_Fit_Score_V2",
        "Opportunity Gap": "Opportunity_Gap_Score_V2",
        "Policy Alignment": "Policy_Alignment_Score_V21",
        "Risk Feasibility": "Risk_Feasibility_Score_V21",
        "Data Reliability": "Data_Reliability_Score_V21",
    }
    calc = 0
    for component, column in columns.items():
        weight = float(weights.loc[weights["Component"] == component, "Weight"].iloc[0])
        calc = calc + weight * pd.to_numeric(master[column], errors="coerce")
    diff = (calc - master["K_ODA_Opportunity_Score_V21"]).abs()
    assert diff.max() <= 0.006


def test_top50_rank_order_is_monotonic() -> None:
    master = pd.read_csv(ROOT / "KODA_master_score_top50_v21.csv")
    assert master["Rank_V21"].is_monotonic_increasing
    assert master["Country_KR"].nunique() == 50
