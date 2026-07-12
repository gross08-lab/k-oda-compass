# AI Upgrade Baseline Report

## Repository

- Branch: `ai-evidence-upgrade`
- Commit: `2cc64ac549526d0ff3f256598296a512b1def1a7`
- Baseline product files were not modified before this capture.

## Test And Score Baseline

- Existing tests: **23 passed**
- Master countries: **50**
- Stored-component weighted score reproduction: **50/50**
- Maximum absolute score error: **0.005000**
- Reproduction boundary: stored seven component scores onward; upstream raw-to-component lineage remains unresolved at baseline.

## Retrieval Baseline

- Mode: lexical/token heuristic in `app.retrieve_rag_evidence`
- Saved scenarios: 3
- Saved Top-K rows: 48
- File: `artifacts/ai_upgrade/baseline_retrieval_results.csv`
- No embedding or hybrid result is claimed in this baseline.

## Generation Baseline

- OPENAI_API_KEY absent: Local RAG fallback executed.
- Generated five output paths: Proposal MD, Brief MD, Evidence Pack MD, Proposal PDF, Brief PDF.
- All output files passed non-empty/signature checks.

## UI Baseline

- Nine top-level views verified in the preserved browser runtime record: True.
- The browser record belongs to the same deployment repository and baseline commit family; it is retained as baseline evidence rather than re-labelled as external validation.

## Frozen Files

- Baseline PDF SHA-256: `22756c2f7197e8f55427c03bd272f8ecde6c6a1619de5dd2f83c06e168512ec6`
- Baseline README SHA-256: `08c0b1db780f653afb889e18e0d54b54e74a83f2ee18d58d9a431fc012ca20a0`

## Known Limits

- Retrieval is lexical/token only.
- External same-model A/B/C experiment has not been executed.
- Raw-data-to-seven-component score lineage is incomplete.
- External expert and user validation are outside this upgrade scope.
