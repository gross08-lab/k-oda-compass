from __future__ import annotations

from typing import Any

import pandas as pd


def stored_component_features(master: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    columns = [config["country_key"], config["iso3_key"]]
    columns.extend(item["column"] for item in config["components"].values())
    result = master[columns].copy()
    for column in columns[2:]:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    return result
