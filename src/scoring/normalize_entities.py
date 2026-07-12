from __future__ import annotations

from typing import Any

import pandas as pd


def validate_country_entities(master: pd.DataFrame, config: dict[str, Any]) -> list[str]:
    errors = []
    country_key = config["country_key"]
    iso3_key = config["iso3_key"]
    if master[country_key].isna().any() or master[country_key].astype(str).str.strip().eq("").any():
        errors.append("blank country key")
    if master[country_key].duplicated().any():
        errors.append("duplicate country key")
    if master[iso3_key].isna().any() or master[iso3_key].astype(str).str.fullmatch(r"[A-Z]{3}").eq(False).any():
        errors.append("invalid ISO3 key")
    return errors
