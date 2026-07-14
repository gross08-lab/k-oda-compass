# Post-submission Engineering Diagnostics

This directory contains reproducibility assets and summarized engineering diagnostics created after the submission benchmark snapshot. Detailed diagnostic dumps that can be mistaken for evaluator-facing KPIs are not published as product documentation.

Use `../screening/canonical_public_kpis.json` for the Live Demo and README public validation surface. The canonical manifest includes only metrics that are reproducible under one current definition and denominator.

## Scope categories

- Current public submission-comparison scope: CPS inventory/searchable corpus, frozen Gold size and Recall@5, stored-component-to-final score/rank reproduction, runtime evidence/export features.
- Post-submission retrieval diagnostics: detailed rank metrics, tuning history, mode comparisons, latency and negative-query behavior.
- Post-submission Citation diagnostics: occurrence counts for named baseline files, structural source-chain checks and deterministic rules.
- Post-submission lineage diagnostics: recovery status from raw sources to stored component scores. This is separate from final score/rank reproduction.
- Post-submission controlled-experiment records: harness inputs and explicit execution status. They are not public performance results unless the recorded calls were actually executed.

Values from different categories must not be combined under one KPI name. Reproduction scripts may create detailed local outputs, but those files must not be committed as public KPIs. Public documentation must resolve validation values through the canonical manifest.
