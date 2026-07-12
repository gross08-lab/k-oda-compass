# Retrieval Benchmark Report

## Gold Set Boundary

- Verified query forms: 60
- Independently checked CPS PDF pages: 10
- Frozen dev/test split: 21/39
- Labels were frozen before any retrieval result was inspected.
- This is an internal benchmark and not an external expert validation.

## Controlled Retrieval Setup

- Embedding model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Runtime: FastEmbed 0.8.0 / mean pooling
- Index: 806 CPS chunks, 1,150,060 bytes
- Build time: 37.954s; model warm-up: 1376.117ms
- Hybrid tuning: dev-only; frozen lexical/embedding weights = 0.2/0.8

## Frozen Test Results

| Mode | Recall@1 | Recall@3 | Recall@5 | MRR | nDCG@5 | Country mismatch | Sector mismatch | Avg ms | p95 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| lexical | 0.680 | 0.960 | 1.000 | 0.817 | 0.863 | 0.000 | 0.000 | 1.50 | 2.19 |
| embedding | 0.400 | 0.480 | 0.520 | 0.448 | 0.466 | 0.621 | 0.374 | 110.51 | 112.44 |
| hybrid | 0.480 | 0.680 | 0.800 | 0.579 | 0.633 | 0.467 | 0.200 | 110.94 | 117.21 |
| hybrid_filtered | 0.640 | 0.840 | 0.960 | 0.755 | 0.806 | 0.000 | 0.000 | 110.44 | 112.50 |

## Decision

- Recommended retrieval mode: `lexical`.
- Recommendation is limited to this frozen internal test set; it is not a universal accuracy claim.
- Negative metadata queries are reported separately and are not counted as positive Recall wins.
- Deployment keeps a deterministic lexical fallback when embedding dependencies or the index are unavailable.
