# CPS Corpus Validation

- Status: **PASS**
- Source PDFs / countries: 27/27
- Pages: 921 total · 652 text layer · 249 OCR searchable · 901 total searchable
- Valid chunks: 1100
- Chunk SHA-256: `dca7c00b0b4610dc5ecd3061547caf25bbe90e5697a896a1f8126322e50d8598`
- Deterministic frame SHA-256: `0aa4449ff243a191a2c7b0f9812557a76c3669f1e256fa8e2c172d4d8372bee2`

| Check | Status | Observed | Expected |
|---|---|---|---|
| pdf_inventory | PASS | 27 | 27 |
| manifest_rows | PASS | 27 | 27 |
| unique_country_codes | PASS | 27 | 27 |
| unique_pdf_country_pairs | PASS | 27 | 27 |
| pdf_sha256 | PASS | see JSON artifact | see JSON artifact |
| all_countries_searchable | PASS | see JSON artifact | see JSON artifact |
| total_pdf_pages | PASS | 921 | 921 |
| direct_extracted_pages | PASS | 652 | 652 |
| ocr_searchable_pages | PASS | 249 | 249 |
| searchable_pages | PASS | 901 | 901 |
| chunk_rows | PASS | 1100 | 1100 |
| valid_chunks | PASS | 1100 | 1100 |
| empty_chunk_text | PASS | 0 | 0 |
| duplicate_chunk_ids | PASS | 0 | 0 |
| page_out_of_range | PASS | 0 | 0 |
| missing_cache_page | PASS | 0 | 0 |
| source_hash_mismatch | PASS | 0 | 0 |
| rebuilt_row_count | PASS | 1100 | 1100 |
| rebuilt_frame_sha256 | PASS | 0aa4449ff243a191a2c7b0f9812557a76c3669f1e256fa8e2c172d4d8372bee2 | 0aa4449ff243a191a2c7b0f9812557a76c3669f1e256fa8e2c172d4d8372bee2 |
