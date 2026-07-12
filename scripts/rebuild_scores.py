from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.scoring.build_component_scores import audited_component_scores
from src.scoring.build_features import stored_component_features
from src.scoring.build_opportunity_score import rebuild_opportunity_score
from src.scoring.load_sources import load_config, load_manifest, load_score_sources, verify_manifest
from src.scoring.normalize_entities import validate_country_entities


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "score_config.yaml")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data" / "data_manifest.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "ai_upgrade" / "rebuilt_scores.csv")
    args = parser.parse_args()
    config = load_config(args.config)
    manifest_errors = verify_manifest(ROOT, load_manifest(args.manifest))
    if manifest_errors:
        raise RuntimeError("manifest verification failed: " + ", ".join(manifest_errors))
    master, weights = load_score_sources(ROOT, config)
    entity_errors = validate_country_entities(master, config)
    if entity_errors:
        raise RuntimeError("entity validation failed: " + ", ".join(entity_errors))
    features = stored_component_features(master, config)
    components, statuses = audited_component_scores(features, config)
    rebuilt = rebuild_opportunity_score(components, weights, config)
    rebuilt["Stored_Opportunity_Score"] = pd.to_numeric(master[config["stored_score"]], errors="raise")
    rebuilt["Stored_Rank"] = pd.to_numeric(master[config["stored_rank"]], errors="raise").astype(int)
    rebuilt["Absolute_Error"] = (rebuilt["Rebuilt_Opportunity_Score"] - rebuilt["Stored_Opportunity_Score"]).abs()
    rebuilt["Rank_Match"] = rebuilt["Rebuilt_Rank"] == rebuilt["Stored_Rank"]
    rebuilt["Raw_To_Component_Reproduced"] = False
    rebuilt["Component_Lineage_Status"] = ";".join(f"{key}:{value}" for key, value in statuses.items())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rebuilt.to_csv(args.output, index=False, encoding="utf-8-sig")
    rebuilt.to_csv(ROOT / "artifacts" / "ai_upgrade" / "score_reproduction_results.csv", index=False, encoding="utf-8-sig")
    print(
        f"countries={len(rebuilt)} aggregate_pass={(rebuilt['Absolute_Error'] <= config['tolerance']).sum()} "
        f"rank_match={rebuilt['Rank_Match'].sum()} max_error={rebuilt['Absolute_Error'].max():.6f} "
        "raw_to_component=0"
    )


if __name__ == "__main__":
    main()
