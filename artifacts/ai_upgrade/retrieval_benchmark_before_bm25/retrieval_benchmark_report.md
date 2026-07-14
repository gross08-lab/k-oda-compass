# Retrieval Benchmark Report

## Gold Set Boundary

- Verified query forms: 120
- Independently checked CPS PDF pages: 27
- Frozen dev/test split: 29/91
- Labels were frozen before any retrieval result was inspected.
- This is an internal benchmark and not an external expert validation.

## Controlled Retrieval Setup

- Embedding model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Runtime: FastEmbed 0.8.0 / mean pooling
- Index: 1100 CPS chunks, 1,569,151 bytes
- Build time: 53.508s; model warm-up: 1339.748ms
- Hybrid tuning: dev-only; frozen lexical/embedding weights = 0.8/0.2

## Frozen Test Results

| Mode | Recall@1 | Recall@3 | Recall@5 | MRR | nDCG@5 | Country mismatch | Sector mismatch | Avg ms | p95 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| lexical | 0.598 | 0.890 | 0.988 | 0.749 | 0.809 | 0.000 | 0.000 | 1.71 | 2.37 |
| embedding | 0.110 | 0.244 | 0.268 | 0.175 | 0.199 | 0.547 | 0.295 | 160.98 | 228.27 |
| hybrid | 0.415 | 0.890 | 0.963 | 0.632 | 0.715 | 0.130 | 0.011 | 153.55 | 163.10 |
| hybrid_filtered | 0.476 | 0.915 | 0.988 | 0.685 | 0.762 | 0.000 | 0.000 | 152.70 | 162.69 |

## Decision

- Recommended retrieval mode: `lexical`.
- Recommendation is limited to this frozen internal test set; it is not a universal accuracy claim.
- Negative metadata queries are reported separately and are not counted as positive Recall wins.
- Deployment keeps a deterministic lexical fallback when embedding dependencies or the index are unavailable.
