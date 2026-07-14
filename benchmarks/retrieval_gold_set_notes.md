# Retrieval Gold Set Notes

## Scope

- Internal frozen Gold Set, not external expert validation.
- Source cases: 27 policy pages across 27 CPS countries.
- Query forms: 120.
- Verified query labels: 120/120.
- Positive queries: 108.
- Negative metadata queries: 12.
- OCR-backed source cases: 7/27.
- Frozen dev/test split: 29/91.

## Label Construction

- One policy-support page was selected per country before retrieval benchmarking.
- Every source Chunk ID is matched to the page cache, country, sector, original PDF SHA-256 and page number.
- Text-layer cases also require a direct normalized substring match to the original PDF text layer.
- OCR cases retain the original PDF hash, file page, OCR method and page cache because image-only pages have no source text layer.
- Four manually written positive query forms are attached to every source page: direct keyword, semantic paraphrase, cross-language and policy alignment.
- Twelve cases add one deliberately mismatched country or sector query to test metadata controls.
- Retrieval outputs are not used to create or change labels.

## Interpretation Boundary

- The 120 value is the number of frozen query forms, not 120 independently reviewed source pages.
- Semantic relevance remains an internal project review, not an external expert judgment.
- OCR-backed labels require the rendered source page to remain available for human spot-checking.
