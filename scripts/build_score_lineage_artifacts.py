from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

from src.scoring.load_sources import sha256_file


ROOT = Path(__file__).resolve().parents[1]


DATASETS = [
    ("master_v21", "K-ODA Compass", "Top50 stored score table", "KODA_master_score_top50_v21.csv", "stored components and final score", "baseline used by app", "PARTIAL"),
    ("weights_v21", "K-ODA Compass", "v2.1 component weights", "KODA_v21_score_weights.csv", "final aggregation weights", "directly used", "VERIFIED"),
    ("score_notes", "K-ODA Compass", "v2.1 score caveats", "KODA_v21_score_notes.csv", "lineage narrative", "documentation only", "PARTIAL"),
    ("koica_projects", "KOICA", "Processed project evidence 2019-2024", "KODA_project_evidence_top50_2019_2024.csv", "cooperation-base evidence", "RAG and profiles", "PARTIAL"),
    ("sector_summary", "KOICA / K-ODA Compass", "Country-sector aggregates 2019-2024", "KODA_country_sector_summary_2019_2024.csv", "sector-fit evidence", "sector exploration", "PARTIAL"),
    ("wdi_latest", "World Bank", "Top50 WDI latest-value long table", "KODA_wdi_latest_top50_long_v2.csv", "development context evidence", "RAG and profiles", "PARTIAL"),
    ("policy_risk", "KOICA integrated indicators / K-ODA Compass", "Policy and risk processed table", "KODA_policy_risk_scores_top50_v21.csv", "policy and risk evidence", "profiles and score audit", "PARTIAL"),
    ("cps_chunks", "KOICA CPS", "CPS searchable chunks", "KODA_cps_pdf_chunks.csv", "policy text evidence", "RAG", "PARTIAL"),
]


def row_count(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return sum(1 for _ in csv.reader(handle)) - 1


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    data_dir = ROOT / "data"
    artifact_dir = ROOT / "artifacts" / "ai_upgrade"
    data_dir.mkdir(exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for dataset_id, provider, title, source_file, role, usage, status in DATASETS:
        path = ROOT / source_file
        manifest.append(
            {
                "dataset_id": dataset_id,
                "provider": provider,
                "title": title,
                "source_file": source_file,
                "source_url": "not preserved in repository metadata",
                "reference_date": "repository snapshot 2026-07-13",
                "coverage_years": "see source file",
                "sha256": sha256_file(path),
                "role": role,
                "current_usage": usage,
                "lineage_status": status,
                "notes": f"processed rows={row_count(path)}; upstream extraction code not preserved unless separately stated",
            }
        )
    write_csv(data_dir / "data_manifest.csv", manifest)

    matrix = [
        {
            "component": "Development Need",
            "input_dataset": "wdi_latest + master_v21",
            "input_columns": "WDI Series Code/Value/Year; Development_Need_Score",
            "transformation": "Narrative says latest WDI values; exact indicator-to-score formula absent",
            "normalization": "UNRESOLVED",
            "direction": "UNRESOLVED per indicator",
            "weight": 0.25,
            "output_range": "stored 0-100",
            "code_location": "final aggregation only: src/scoring/build_opportunity_score.py",
            "evidence_file": "KODA_v21_score_notes.csv; docs/model_card.md",
            "status": "PARTIAL",
            "notes": "Ten WDI codes are present, but their upstream use in this component is not proven by executable lineage.",
        },
        {
            "component": "Korea Cooperation Base",
            "input_dataset": "koica_projects + master_v21",
            "input_columns": "processed project records and aggregate fields; Korea_Coop_Base_Score_V2",
            "transformation": "Narrative says record/disbursement history; exact formula absent",
            "normalization": "UNRESOLVED",
            "direction": "higher stored score means stronger base",
            "weight": 0.20,
            "output_range": "stored 0-100",
            "code_location": "final aggregation only: src/scoring/build_opportunity_score.py",
            "evidence_file": "KODA_v21_score_notes.csv",
            "status": "PARTIAL",
            "notes": "Stable source project ID is unavailable; processed record count is not a unique-project count.",
        },
        {
            "component": "Sector Fit",
            "input_dataset": "sector_summary + master_v21",
            "input_columns": "country-sector-year aggregates; Sector_Fit_Score_V2",
            "transformation": "Narrative says multi-year sector pattern; exact formula absent",
            "normalization": "UNRESOLVED",
            "direction": "higher stored score means stronger fit",
            "weight": 0.15,
            "output_range": "stored 0-100",
            "code_location": "final aggregation only: src/scoring/build_opportunity_score.py",
            "evidence_file": "KODA_v21_score_weights.csv",
            "status": "PARTIAL",
            "notes": "Current sector opportunity UI does not recreate the country component.",
        },
        {
            "component": "Opportunity Gap",
            "input_dataset": "master_v21",
            "input_columns": "Opportunity_Gap_Score_V2",
            "transformation": "Meaning documented as need versus additional opportunity; exact inputs and formula absent",
            "normalization": "UNRESOLVED",
            "direction": "UNRESOLVED",
            "weight": 0.10,
            "output_range": "stored 0-100",
            "code_location": "final aggregation only: src/scoring/build_opportunity_score.py",
            "evidence_file": "KODA_v21_score_weights.csv",
            "status": "UNRESOLVED",
            "notes": "No upstream code or independent source columns were found.",
        },
        {
            "component": "Policy Alignment",
            "input_dataset": "policy_risk + master_v21",
            "input_columns": "CPS target, office, support and sector subscore columns",
            "transformation": "Processed subcomponents are preserved; their combination formula is absent",
            "normalization": "subscores stored; source normalization code absent",
            "direction": "higher stored score means stronger alignment",
            "weight": 0.15,
            "output_range": "stored 0-100",
            "code_location": "final aggregation only: src/scoring/build_opportunity_score.py",
            "evidence_file": "KODA_policy_risk_scores_top50_v21.csv",
            "status": "PARTIAL",
            "notes": "CPS PDF RAG evidence is not proven to be an upstream score input.",
        },
        {
            "component": "Risk Feasibility",
            "input_dataset": "policy_risk + master_v21",
            "input_columns": "fragility, corruption, e-government, HDI, business and office subscores",
            "transformation": "Raw and processed subscore values coexist; exact normalization and combination code absent",
            "normalization": "PARTIAL narrative only",
            "direction": "fragility reversed; other directions documented narratively",
            "weight": 0.10,
            "output_range": "stored 0-100",
            "code_location": "final aggregation only: src/scoring/build_opportunity_score.py",
            "evidence_file": "KODA_policy_risk_scores_top50_v21.csv; KODA_v21_score_notes.csv",
            "status": "PARTIAL",
            "notes": "No inferred weights or fitted formula are used.",
        },
        {
            "component": "Data Reliability",
            "input_dataset": "master_v21 + policy_risk + wdi_latest",
            "input_columns": "WDI_Core_Coverage_%; Policy_Risk_Data_Coverage_%; Data_Reliability_Score_V21",
            "transformation": "Coverage inputs are visible; exact combination formula absent",
            "normalization": "UNRESOLVED",
            "direction": "higher coverage expected to mean higher reliability",
            "weight": 0.05,
            "output_range": "stored 0-100",
            "code_location": "final aggregation only: src/scoring/build_opportunity_score.py",
            "evidence_file": "KODA_master_score_top50_v21.csv",
            "status": "PARTIAL",
            "notes": "App displays coverage but does not regenerate the component.",
        },
        {
            "component": "Opportunity Score",
            "input_dataset": "master_v21 + weights_v21",
            "input_columns": "seven stored component scores and published weights",
            "transformation": "weighted sum",
            "normalization": "none after weighted sum",
            "direction": "higher means higher preliminary review priority",
            "weight": 1.00,
            "output_range": "0-100",
            "code_location": "src/scoring/build_opportunity_score.py",
            "evidence_file": "KODA_v21_score_weights.csv; tests/test_score_model.py",
            "status": "VERIFIED",
            "notes": "Reproduces stored score within rounding tolerance using stored components; not a raw-to-score reproduction.",
        },
    ]
    write_csv(artifact_dir / "score_lineage_matrix.csv", matrix)
    counts = pd.Series([row["status"] for row in matrix]).value_counts().to_dict()
    (artifact_dir / "score_lineage_audit_summary.json").write_text(
        json.dumps({"matrix_status_counts": counts, "raw_to_component_verified": 0}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    main()
