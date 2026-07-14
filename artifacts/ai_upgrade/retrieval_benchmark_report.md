# Retrieval Benchmark Report

## Gold Set Boundary

- Verified query forms: 120
- Independently checked CPS PDF pages: 27
- Frozen dev/test split: 29/91
- Gold label fingerprint: `c42d43130647b074d5c8e6b7b856aef44009a549f768f17433506792821d0446`
- Test labels and split were verified before this final run.
- This is an internal benchmark and not an external expert validation.

## Controlled Retrieval Setup

- Lexical ranker: `candidate-local-bm25-idf`
- Embedding model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Index: 1100 CPS chunks, 1,569,151 bytes
- Build time: 53.508s; model warm-up: 1480.371ms
- Dev-selected frozen lexical/embedding weights: 1.00/0.00
- Dev-selected frozen phrase bonus: 1.50

## Frozen Test Results

| Mode | Recall@1 | Recall@3 | Recall@5 | MRR | nDCG@5 | Country mismatch | Sector mismatch | Avg ms | p95 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| lexical | 0.537 | 0.878 | 1.000 | 0.716 | 0.787 | 0.000 | 0.000 | 0.57 | 0.76 |
| embedding | 0.110 | 0.244 | 0.268 | 0.175 | 0.199 | 0.547 | 0.295 | 37.67 | 52.46 |
| hybrid | 0.476 | 0.817 | 0.963 | 0.656 | 0.733 | 0.220 | 0.035 | 37.23 | 51.21 |
| hybrid_filtered | 0.537 | 0.878 | 1.000 | 0.716 | 0.787 | 0.000 | 0.000 | 11.59 | 16.96 |

## Decision

- Operational retrieval mode: `hybrid_filtered` (frozen before final Test evaluation).
- Results are limited to this frozen internal test set; they are not a universal accuracy claim.
- Negative metadata queries are reported separately and are not counted as positive Recall wins.
- Deployment keeps a deterministic lexical fallback when embedding dependencies or the index are unavailable.
