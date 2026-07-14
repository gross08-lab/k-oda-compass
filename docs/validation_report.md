# Public Validation Report

This report uses `artifacts/screening/canonical_public_kpis.json` as the only evaluator-facing KPI definition. It covers results that can be reproduced with the current repository under the same denominator and scope.

## Public KPI Snapshot

| Area | Result | Exact scope | Status |
|---|---|---|---|
| CPS inventory | 27 PDFs / 27 searchable countries / 921 pages | Repository PDF manifest | VERIFIED |
| CPS searchable corpus | 652 direct + 249 OCR = 901 searchable pages; 1,100 valid chunks | Blank chunks and 20 unsearchable pages excluded | VERIFIED |
| Gold integrity | 120 queries; Dev 29 / Test 91; frozen label fingerprint | Frozen Gold file and split | VERIFIED |
| Frozen Test retrieval | Recall@5 1.000 | 82 positive Test queries with expected evidence | VERIFIED |
| Final score/rank reproduction | 50/50 countries; maximum absolute error 0.005 | Stored seven component scores to final score and rank | VERIFIED |
| Runtime evidence path | Evidence ID, CPS document/page, Evidence Pack, A01-A07 | Representative Local RAG Builder scenario | VERIFIED |
| Export path | Proposal MD, Brief MD, Evidence Pack MD, Proposal PDF, Brief PDF | API-key-free default path | VERIFIED |
| Streamlit runtime | 9/9 top-level views and Local RAG generation without an API key | Streamlit AppTest | VERIFIED |
| Automated tests | See canonical manifest | Current repository test suite | VERIFIED |

## Scope Boundary

Post-submission retrieval diagnostics, baseline-output Citation occurrence counts, raw-source-to-component lineage recovery, external-model controlled-experiment records, and human semantic-judgment records use different evaluation populations or execution conditions. They remain under `artifacts/ai_upgrade/` for engineering traceability and are not merged into, substituted for, or displayed as the public submission-comparison KPI.

This separation prevents unlike denominators from appearing as conflicting values while preserving the raw diagnostic artifacts. It does not assert that an unexecuted or differently scoped validation was completed.

## Reproduction Sources

- `artifacts/ai_upgrade/cps_corpus_validation.json`
- `artifacts/ai_upgrade/retrieval_gold_freeze.json`
- `artifacts/ai_upgrade/retrieval_benchmark_summary.json`
- `artifacts/ai_upgrade/score_reproduction_results.csv`
- `tests/test_app_runtime_smoke.py`
- `tests/test_builder_outputs.py`
- `tests/test_screening_consistency.py`

Run `pytest -q` and `python3 -m py_compile app.py` from the repository root. The public URL and QR destinations are recorded separately in `artifacts/screening/live_access_check.json` because CI tests must not depend on an external network response.
