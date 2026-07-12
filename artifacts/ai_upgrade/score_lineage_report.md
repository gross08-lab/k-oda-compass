# Score Lineage Audit Report

## Audit Scope

The audit searched the current branch, all local and remote-tracking branches, every reachable Git commit and object, the similar deployment copy, repository scripts, notebooks, CSV files, Markdown documentation, score notes, and the surrounding project workspace.

No executable upstream pipeline was found for converting raw WDI, KOICA, CPS, and policy-risk observations into the seven stored component scores. No deleted or historical score-generation script was present in the reachable Git history.

## Status By Stage

| Stage | Status | Evidence boundary |
|---|---|---|
| Development Need | PARTIAL | WDI latest-value records and stored score exist; indicator selection, direction, missing-value, normalization, and combination formula are not executable |
| Korea Cooperation Base | PARTIAL | KOICA processed records and stored score exist; unique-project rule, amount handling, normalization, and formula are absent |
| Sector Fit | PARTIAL | Country-sector-year aggregates exist; component formula is absent |
| Opportunity Gap | UNRESOLVED | Only stored score and high-level meaning remain |
| Policy Alignment | PARTIAL | Raw indicators and processed subscores coexist; normalization and subscore combination formula are absent |
| Risk Feasibility | PARTIAL | Raw indicators, direction narrative, and processed subscores exist; exact normalization and weights are absent |
| Data Reliability | PARTIAL | Coverage fields and stored score exist; exact combination formula is absent |
| Opportunity Score | VERIFIED | Seven stored component scores multiplied by published weights reproduce the final score |

Matrix count: `VERIFIED 1`, `PARTIAL 6`, `UNRESOLVED 1`. The verified item is the final aggregation stage, not a raw-to-component reconstruction.

## Reproduction Result

- Countries: 50
- Stored-component weighted aggregation within tolerance: 50/50
- Maximum absolute score error: 0.005
- Rank matches: 50/50
- Raw-to-component fully reproduced countries: 0

The implementation intentionally preserves stored component values as the baseline. It does not fit, reverse-engineer, or substitute a plausible upstream formula.

## Reproduction

```bash
PYTHONPATH=. python3 scripts/build_score_lineage_artifacts.py
PYTHONPATH=. python3 scripts/rebuild_scores.py
```

The manifest verifies hashes before the aggregation is run. `score_lineage_matrix.csv` is the authoritative record of what is and is not reproducible.
