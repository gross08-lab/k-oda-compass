from __future__ import annotations

from typing import Any

import pandas as pd


def audited_component_scores(features: pd.DataFrame, config: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, str]]:
    """Return stored components without claiming an unavailable upstream rebuild."""
    statuses = {name: item["lineage_status"] for name, item in config["components"].items()}
    if any(status == "VERIFIED" for status in statuses.values()):
        raise ValueError("No component is VERIFIED from raw input in the audited repository snapshot")
    return features.copy(), statuses
