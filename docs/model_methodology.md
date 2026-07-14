# Model Methodology

## Opportunity Score

The app reproduces the stored v2.1 final aggregation:

`KODA = 0.25D + 0.20K + 0.15S + 0.10G + 0.15P + 0.10F + 0.05R`

where D is Development Need, K Korea Cooperation Base, S Sector Fit, G Opportunity Gap, P Policy Alignment, F Risk Feasibility, and R Data Reliability.

Using the seven stored component columns and `KODA_v21_score_weights.csv`, 50/50 scores and 50/50 ranks reproduce with maximum absolute error 0.005. This verifies final aggregation only.

## Upstream Boundary

| Stage | Status | Reason |
|---|---|---|
| Seven stored components to final score | VERIFIED | Executable weighted sum and rank reproduction |
| Development Need | PARTIAL | WDI values exist; exact indicator-to-score formula is absent |
| Korea Cooperation Base | PARTIAL | Processed records exist; exact aggregation and stable project ID are absent |
| Sector Fit | PARTIAL | Sector aggregates exist; upstream component formula is absent |
| Opportunity Gap | UNRESOLVED | Independent inputs and formula are absent |
| Policy Alignment | PARTIAL | Stored subcomponents exist; upstream normalization/combination code is absent |
| Risk Feasibility | PARTIAL | Raw and processed fields coexist; exact normalization/combination is absent |
| Data Reliability | PARTIAL | Coverage fields exist; exact combination formula is absent |

No fitted formula, inverse reconstruction, or hardcoded country exception is used to convert these statuses to VERIFIED. Run `scripts/build_score_lineage_artifacts.py` and `scripts/rebuild_scores.py` to reproduce the audit.

## Decision Boundary

The score is a preliminary review priority, not automatic project selection. Changes in weights, source freshness, missing data, CPS version and local evidence must be reviewed by a person.
