from __future__ import annotations

from typing import Any

import pandas as pd


def rebuild_opportunity_score(
    component_scores: pd.DataFrame,
    weights: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    lookup = dict(zip(weights["Component"], pd.to_numeric(weights["Weight"], errors="raise")))
    if abs(sum(float(value) for value in lookup.values()) - 1.0) > 1e-12:
        raise ValueError("score weights must sum to 1")
    score = pd.Series(0.0, index=component_scores.index)
    for component, item in config["components"].items():
        score = score + pd.to_numeric(component_scores[item["column"]], errors="raise") * float(lookup[component])
    result = component_scores[[config["country_key"], config["iso3_key"]]].copy()
    result["Rebuilt_Opportunity_Score"] = score
    result["Rebuilt_Rank"] = score.rank(ascending=False, method="first").astype(int)
    return result
