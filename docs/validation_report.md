# Validation Report

## Actual KPI Snapshot

| Area | Result | Status |
|---|---|---|
| CPS inventory | 27 PDFs / 27 countries / 921 pages | VERIFIED |
| CPS searchable corpus | 652 direct + 249 OCR = 901 pages; 1,100 valid chunks | VERIFIED |
| Gold integrity | 120 queries; Dev 29 / Test 91; frozen hash and labels | VERIFIED |
| Filtered retrieval Test | Recall@5 1.000; MRR 0.716; nDCG@5 0.787 | VERIFIED internal benchmark |
| Negative rejection | 1/9 | LIMIT |
| Final score/rank reproduction | 50/50; max absolute error 0.005 | VERIFIED final aggregation |
| Raw-to-component score lineage | 1 VERIFIED, 6 PARTIAL, 1 UNRESOLVED including final output row | PARTIAL |
| Citation structure | 47/47 current baseline occurrences; excluded-ID misuse 0 | VERIFIED structural scope |
| Original PDF Citation spot-check | 17/17 exact normalized text matches | VERIFIED sample scope |
| Claim-Citation human judgments | 0; kappa unavailable | UNRESOLVED |
| Controlled A/B/C | 0/30 API calls without a key | UNRESOLVED |
| Streamlit runtime | 9/9 top-level views + Local RAG Builder generation without API key | VERIFIED via AppTest |
| Automated tests | 54 passed | VERIFIED |
| Final proposal PDF | 10/10 A4 nonblank pages; required metrics present; stale/secret hits 0 | VERIFIED except QR image re-decode |

## Retrieval Comparison

The official final four-mode table is `artifacts/ai_upgrade/retrieval_benchmark_summary.csv`. Before/after evidence is retained in `retrieval_benchmark_history.*` and `retrieval_benchmark_before_bm25/`. Test labels were not altered. All positive filtered queries retrieved an expected chunk in Top 5; eight of nine negative Test queries still returned candidates.

## Citation Scope

`scripts/audit_citations.py` checks Evidence existence, Evidence Pack inclusion, excluded-ID misuse, CPS document existence, page range, page cache, country, original PDF hash and chunk source hash. The deterministic source-type rules returned no review row for the current baseline, but this does not replace human factual-support judgment.

## Generation Experiment

The 10-case, three-condition harness and deterministic evaluator are implemented. The current run had no `OPENAI_API_KEY`, so it produced 30 `NOT_EXECUTED_NO_API_KEY` records and zero measured quality, latency, token or cost gains. Mock values are not reported as measurements.

## Final Submission PDF

`scripts/qa_ai_upgrade_submission.py` validates the regenerated 10-page PDF and writes `artifacts/proposal/final_submission_ai_upgrade/qa_automated_results.json`. The PDF SHA-256 is `f02fe735ef3d7ec0bb3d8aa9ac5f397dfe93422df3f19d788ddd2eb72277d728`. Streamlit and GitHub link annotations match the public URLs. Direct QR image re-decoding was blocked by the local Vision runtime, so only QR source payload, visible render and link annotations are verified in this run.
