# Public Validation Scope

The single evaluator-facing KPI source is `artifacts/screening/canonical_public_kpis.json`. The Streamlit overview and validation screen load this manifest at runtime, and the README links to the same file without maintaining a second numeric snapshot.

The manifest records definitions, denominators, provenance files and the verification date for the current public scope. Submission-time frozen validation and post-submission engineering diagnostics are kept conceptually separate because their inputs or execution conditions may differ.

Internal retrieval comparisons, baseline Citation occurrence counts, lineage-recovery status, controlled-experiment execution records and human-review work products are not Live Demo KPIs. Their existence must not be interpreted as a replacement for, or revalidation of, the submission-time claims.

## Reproduction

```bash
python3 -m py_compile app.py
pytest -q
```

Public URLs and the QR destination check are recorded in `artifacts/screening/live_access_check.json`. API-key-free Local RAG remains the default reproducible generation path.
