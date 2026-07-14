# Retrieval Benchmark History

| Phase | Recall@5 | MRR | nDCG@5 | Evidence status |
|---|---:|---:|---:|---|
| Initial filtered hybrid | 0.890 | 0.631 | 0.697 | Captured command output; overwritten raw CSV unavailable |
| Term expansion before BM25 | 0.988 | 0.685 | 0.762 | Raw artifacts preserved in `retrieval_benchmark_before_bm25/` |
| Final candidate-local BM25/IDF | 1.000 | 0.716 | 0.787 | Raw final artifacts in the parent directory |

All comparable values use the frozen 91-query Test split. The final parameters were selected on the 29-query Dev split. Gold SHA-256, split, and expected chunk IDs are guarded by `scripts/verify_retrieval_gold_freeze.py`. The final operating weight is lexical 1.0 and embedding 0.0 because the local embedding model reduced Dev ranking quality; the result is reported transparently rather than described as an embedding gain.

The initial phase is not used as a reproducible official result because its raw artifact was overwritten before interruption. The final phase is the official measured result.
