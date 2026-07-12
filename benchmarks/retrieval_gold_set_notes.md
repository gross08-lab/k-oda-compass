# Retrieval Gold Set Notes

## Scope

- Internal validation Gold Set, not external expert validation.
- Queries: 60
- Verified queries: 60
- Positive queries: 40
- Negative metadata queries: 20
- Countries represented by positive labels: 10
- Sectors represented by positive labels: 5
- Dev/Test split: 21/39

## Label Construction

- Ten CPS chunk IDs were selected before retrieval benchmarking.
- Each selected chunk was compared with the corresponding original PDF file page.
- `label_verified=true` only when normalized committed chunk text was a substring of normalized PDF page text.
- Direct, semantic, cross-language and policy-alignment queries were written from the verified source passage.
- Negative-country and negative-sector queries retain the source meaning but deliberately apply mismatched metadata; they test whether retrieval promotes semantically tempting but metadata-inconsistent evidence.
- Retrieval outputs were not used to create or change labels.

## Interpretation Boundary

- The set is an internal deterministic benchmark, not a representative sample of every CPS question.
- One verified source page per country is expanded into six query forms, so query-level confidence does not equal 60 independent source-page reviews.
- Negative queries are evaluated mainly through mismatch and rejection behavior, not positive Recall.
