# Data Card

## Sources

- KOICA ODA project evidence, 2019-2024
- World Bank WDI latest values, 2019-2025 window
- KOICA integrated partner-country development indicators used as policy/risk proxy
- Korean CPS PDF text chunks extracted from `CPS(kor)` files
- K-ODA Compass v2.1 score weights and notes

## Processed Files

- `KODA_master_score_top50_v21.csv`: Top 50 country score table
- `KODA_project_evidence_top50_2019_2024.csv`: KOICA project evidence corpus
- `KODA_wdi_latest_top50_long_v2.csv`: WDI indicator corpus
- `KODA_policy_risk_scores_top50_v21.csv`: policy/risk proxy table
- `KODA_cps_pdf_chunks.csv`: page-level CPS PDF RAG chunks
- `KODA_cps_pdf_ocr_coverage.csv`: CPS PDF text-layer and OCR target audit
- `KODA_country_sector_summary_2019_2024.csv`: country-sector portfolio summary
- `KODA_v21_score_weights.csv`: score model weights
- `KODA_v21_score_notes.csv`: model caveats

## Quality Checks

- Duplicate rows are checked in tests.
- Score formula is recalculated from weights.
- Country coverage is checked across score, WDI, policy/risk, and KOICA evidence files.
- CPS PDF chunk uniqueness, text length, and top-country overlap are checked in tests.
- CPS PDF text-layer coverage is audited in `docs/cps_ocr_coverage.md`.
- Missing WDI and policy/risk values are exposed rather than silently imputed.

## Known Caveats

- Raw commitment/disbursement values are displayed as raw values until official unit metadata is reconfirmed.
- CPS alignment combines parsed CPS PDF chunks and public CSV proxy fields. As of the local OCR audit, 663/921 CPS pages are readable via text layer and 7 image-only PDFs require Tesseract/OCR for full-text coverage.
- Project descriptions can contain heterogeneous formatting from source data.
