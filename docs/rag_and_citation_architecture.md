# RAG and Citation Architecture

## CPS Pipeline

1. Preserve 27 original CPS PDFs and SHA-256 values.
2. Select the better direct text from pypdf/pdfplumber.
3. Apply macOS Vision or Tesseract OCR to noisy/image pages.
4. Exclude pages that remain noisy or empty.
5. Chunk each searchable page at 1,024 target characters with 120-character overlap.
6. Assign deterministic `CPS-{ISO3}-p{page}-{chunk}` IDs and retain PDF, page, extraction method and source hash.

The final corpus contains 901 searchable pages and 1,100 valid chunks across 27 countries.

## Lexical Ranking

For the metadata-filtered candidate set, the ranker computes:

- BM25 IDF: `ln(1 + (N - df + 0.5) / (df + 0.5))`.
- BM25 parameters: `k1=1.2`, `b=0.75`.
- Query-term coverage bonus: 2.0 per matched unique term.
- Dev-selected phrase-frequency bonus: 1.5, capped at three occurrences per phrase term.
- General country/sector/source metadata bonuses and deterministic Chunk-ID tie-breaking.

English ODA terms are expanded through a general domain dictionary. There are no query-ID, Gold Chunk-ID, country-page or answer-text exceptions.

Filtered hybrid normalizes lexical and embedding scores inside the filtered candidate set. Dev tuning selected lexical/embedding weights 1.0/0.0 because the fixed local embedding model reduced ranking quality. The app therefore keeps lexical as its lightweight default while retaining embedding and hybrid as optional, auditable modes.

## Frozen Benchmark

- Gold: 120 verified query forms, Dev 29 / Test 91.
- Gold SHA-256: `796d6293687f76a2f43b318f5ccd4cf7e2ef06d2c7892d41cfdb3585bdbf3159`.
- Label/split fingerprint: `c42d43130647b074d5c8e6b7b856aef44009a549f768f17433506792821d0446`.
- Final filtered Test: Recall@5 1.000, MRR 0.716, nDCG@5 0.787.
- Negative rejection: 1/9; this remains a known limitation.

## Evidence and Citation

All Builder outputs share a structured result containing Evidence objects, assumptions and generated text. Classes are `Source Evidence`, `Supplementary Source`, `Derived Evidence`, `Model Output`, and `AI Design Assumption`. Proposal-excluded evidence remains visible in the Evidence Pack but cannot be cited by Proposal or Brief.

The current structural audit resolves 47/47 Citation occurrences across the baseline Proposal, Brief and Evidence Pack. Three CPS objects pass document/page/cache/hash checks, and 17 prior original-PDF text spot-checks are exact after normalization. A 120-pair human Claim-Citation table and Cohen's kappa were not found; semantic accuracy is therefore not claimed as externally or independently validated.
