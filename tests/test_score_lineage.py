from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.scoring.build_component_scores import audited_component_scores
from src.scoring.build_features import stored_component_features
from src.scoring.build_opportunity_score import rebuild_opportunity_score
from src.scoring.load_sources import load_config, load_manifest, load_score_sources, verify_manifest
from src.scoring.normalize_entities import validate_country_entities


ROOT = Path(__file__).resolve().parents[1]


def test_manifest_hashes_match_current_sources() -> None:
    manifest = load_manifest(ROOT / "data" / "data_manifest.csv")
    assert verify_manifest(ROOT, manifest) == []


def test_lineage_statuses_do_not_overclaim_raw_reproduction() -> None:
    config = load_config(ROOT / "config" / "score_config.yaml")
    statuses = {item["lineage_status"] for item in config["components"].values()}
    assert statuses <= {"PARTIAL", "UNRESOLVED"}
    summary = json.loads((ROOT / "artifacts" / "ai_upgrade" / "score_lineage_audit_summary.json").read_text(encoding="utf-8"))
    assert summary["raw_to_component_verified"] == 0


def test_final_aggregation_reproduces_all_countries() -> None:
    config = load_config(ROOT / "config" / "score_config.yaml")
    master, weights = load_score_sources(ROOT, config)
    assert validate_country_entities(master, config) == []
    features = stored_component_features(master, config)
    components, _ = audited_component_scores(features, config)
    rebuilt = rebuild_opportunity_score(components, weights, config)
    error = (rebuilt["Rebuilt_Opportunity_Score"] - master[config["stored_score"]]).abs()
    assert len(rebuilt) == 50
    assert int((error <= config["tolerance"]).sum()) == 50
    assert int((rebuilt["Rebuilt_Rank"] == master[config["stored_rank"]]).sum()) == 50
