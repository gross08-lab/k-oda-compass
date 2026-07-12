# K-ODA Compass Final AI Technical Upgrade Report

## Work Result

Result: **partial success with submission-ready outputs**.

Retrieval implementation, internal benchmarking, score-lineage audit, app integration, tests, and the 10-page proposal are complete. The same-model A/B/C harness and evaluator are complete, but actual model calls were not executed because no API key was available. No unexecuted result is represented as measured performance.

## Branch And Baseline

- Branch: `ai-evidence-upgrade`
- Baseline commit: `2cc64ac549526d0ff3f256598296a512b1def1a7`
- Baseline tests: 23 passed
- Final tests before Git snapshot: 38 passed
- Baseline score reproduction: 50/50, maximum absolute error 0.005
- Existing Local RAG, five output paths, nine top-level views, and lexical retrieval were preserved.

## Retrieval Architecture

Four modes are implemented with one result schema: lexical, embedding, hybrid, and metadata-filtered hybrid. The optional embedding model is `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, FastEmbed 0.8.0 mean pooling, 384 dimensions, Apache-2.0. The model is local and optional; its 235 MB ONNX/cache files are ignored by Git.

The committed reproducible index contains 806 CPS chunks, is 1,150,060 bytes, and records the chunk-source SHA-256. Index build time was 37.954 seconds. Model warm-up was 1,376.117ms and is excluded from per-query latency.

If FastEmbed, the model, or a current index is unavailable, the app reports the reason and returns to lexical retrieval. The Streamlit app does not load the embedding model at startup.

## Gold Set

- Verified query forms: 60
- Independently checked CPS PDF pages: 10
- Countries: 10
- Query forms per page: direct keyword, semantic paraphrase, cross-language, policy alignment, negative country, negative sector
- Split frozen before benchmark: dev 21 / test 39
- External expert validation: no

The 60 value is not described as 60 independent source-page reviews. Every positive label is tied to a committed Chunk ID and a CPS PDF page whose normalized source text was directly matched.

## Retrieval Benchmark

Frozen test results:

| Mode | Recall@1 | Recall@3 | Recall@5 | MRR | nDCG@5 | Country mismatch | Sector mismatch | Avg ms | p95 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| lexical | 0.68 | 0.96 | 1.00 | 0.817 | 0.863 | 0.000 | 0.000 | 1.50 | 2.19 |
| embedding | 0.40 | 0.48 | 0.52 | 0.448 | 0.466 | 0.621 | 0.374 | 110.51 | 112.44 |
| hybrid | 0.48 | 0.68 | 0.80 | 0.579 | 0.633 | 0.467 | 0.200 | 110.94 | 117.21 |
| hybrid_filtered | 0.64 | 0.84 | 0.96 | 0.755 | 0.806 | 0.000 | 0.000 | 110.44 | 112.50 |

Hybrid weights were selected on dev only and frozen at lexical 0.2 / embedding 0.8. Test results were not used for retuning.

Embedding improved first-rank retrieval for examples including Indonesian e-government and Ugandan cross-language education queries. Lexical was materially better on multiple Bangladesh energy, Senegal agriculture, Nepal health, and Vietnam policy queries. All modes returned records for the deliberately mismatched negative metadata queries, so negative rejection was 0%. This limitation is retained in the report and proposal.

Decision: lexical remains the operating default because it had the strongest test accuracy, zero metadata mismatch, and the lowest latency. Embedding and hybrid remain optional comparison modes.

## Controlled A/B/C Experiment

The harness fixes the same planned model identifier, user input, country, sector, output sections, timeout, token ceiling, case set, and deterministic evaluator across:

- `GENERIC`: user request only
- `RAW_EVIDENCE`: the same request plus CPS source text
- `KODA_CONTROLLED`: the same request plus stored score, Evidence Pack, Evidence Class, Citation rules, A01-A07 assumptions, and additional-research rules

Cases: 10. Conditions: 3. Planned calls: 30. Executed calls: 0. Status: `NOT_EXECUTED_NO_API_KEY`.

The evaluator implements Citation coverage, invalid Evidence ID, assumption separation, unsupported numeric-claim screening, and section completeness. Semantic support remains REVIEW where human source judgment is needed. Latency, token usage, cost, Citation improvement, unsupported-claim change, and assumption-separation change were not measured.

## Score Lineage

The audit searched all reachable Git commits and objects, current and remote-tracking branches, the similar deployment copy, scripts, notebooks, processed data, score notes, and the surrounding workspace.

No executable raw-to-seven-component pipeline was found. The audit did not reverse-fit or substitute a plausible formula.

- VERIFIED: final Opportunity Score weighted aggregation, 1 stage
- PARTIAL: Development Need, Korea Cooperation Base, Sector Fit, Policy Alignment, Risk Feasibility, Data Reliability, 6 stages
- UNRESOLVED: Opportunity Gap, 1 stage
- Raw-to-component fully reproduced countries: 0
- Stored-component final score reproduced: 50/50
- Rank reproduced: 50/50
- Maximum absolute error: 0.005

## App Integration

- AI Builder exposes lexical, embedding, hybrid, and filtered-hybrid CPS retrieval modes.
- The default is lexical, explicitly tied to the internal benchmark.
- Requested and effective retrieval modes are shown in the UI and output metadata.
- Missing optional dependencies or stale/missing index conditions produce an explicit lexical fallback.
- Existing segmented navigation, view-level lazy loading, 900-second caches, Plotly lazy imports, country-scoped RAG construction, Local RAG fallback, and five output paths remain intact.

Local runtime QA without `OPENAI_API_KEY` opened all nine views, generated a Local RAG proposal, exercised no-key LLM fallback, and exercised embedding-to-lexical fallback without an app crash.

## Proposal And PDF QA

- Final PDF: `artifacts/proposal/final_submission_ai_upgrade/KODA_Compass_Proposal_FINAL_SUBMISSION_AI_UPGRADE.pdf`
- Pages: exactly 10 A4 pages
- File size: 7,714,262 bytes
- Rendering: 10/10 pages at 200 dpi, all nonblank
- Korean text: visually intact; subset Korean fonts embedded
- Live Demo link and QR: verified
- GitHub link and QR: verified
- Forbidden proposal phrases: 0
- Secret/API key patterns: 0
- Local absolute paths in PDF: 0

Pages 1-6 preserve the supplied design. Page 4 now states that lexical is the operating default and embedding/hybrid are optional. Page 7 remains model-neutral because A/B/C was not executed. Page 8 reports the retrieval benchmark and lineage limits. Pages 9-10 remove embedding implementation from future-work claims and retain OCR, external validation, and institutional pilot work as plans.

## Test Summary

- Python compilation: PASS
- Pytest: 38 passed
- Score manifest hashes: PASS
- Retrieval schema, metrics, index staleness, fallback, app integration, controlled-input equality, unsupported numeric claims, A-ID separation, and score rebuild regression: PASS
- Streamlit local runtime: PASS
- `git diff --check`: PASS at final review

## Remaining Limits

- Seven image-centered CPS PDFs require OCR.
- The Gold Set is internal and limited to 10 independently checked source pages.
- Negative metadata-query rejection is not solved by the tested retrieval modes.
- The seven raw-to-component score formulas remain partially or wholly unresolved.
- Actual same-model A/B/C generation was not executed.
- External expert review, institutional pilot, field demand validation, and willingness-to-pay testing remain future work.

## Submission Decision

The code, benchmark, lineage disclosure, app fallback, and final 10-page PDF are internally consistent and ready for submission. Submission is **conditionally possible** because the package is technically complete, while A/B/C generation results, full OCR coverage, and external validation must remain described as unfinished.
