# Data Catalog

## Current Product Inputs

| Layer | File | Unit | Current size | Role | Lineage status |
|---|---|---|---:|---|---|
| Core ODA | `KODA_project_evidence_top50_2019_2024.csv` | KOICA processed record | 12,436 | Korean cooperation experience and project evidence | PARTIAL upstream lineage |
| Core policy | `data/cps_pdfs/*.pdf` | Original CPS PDF | 27 PDFs / 27 countries | Policy source document | VERIFIED inventory and SHA |
| Core policy | `data/cps_page_text.csv` | Searchable page | 901 | Direct extraction or OCR page cache | VERIFIED |
| Core policy | `KODA_cps_pdf_chunks.csv` | RAG chunk | 1,100 valid | Page Citation and lexical retrieval | VERIFIED |
| Supplementary | `KODA_wdi_latest_top50_long_v2.csv` | Country-indicator latest row | 500 rows / 481 values | Country development-context signal | VERIFIED as supplementary data; score upstream unresolved |
| Supplementary | `KODA_policy_risk_scores_top50_v21.csv` | Country row | 50 | Policy and execution-environment supporting indicators | PARTIAL upstream lineage |
| Derived | `KODA_country_sector_summary_2019_2024.csv` | Country-sector aggregate | 669 | Past cooperation portfolio | PARTIAL upstream lineage |
| Model input/output | `KODA_master_score_top50_v21.csv` | Country | 50 | Seven stored components, Opportunity Score and rank | Final aggregation VERIFIED; component creation PARTIAL/UNRESOLVED |

## CPS Coverage

- Physical PDF pages: 921.
- Directly extracted pages in the final page cache: 652.
- OCR-backed searchable pages: 249.
- Total searchable pages: 901; unsearchable pages: 20.
- Searchable CPS countries: 27/27.
- Top50 intersection: 26/50. India (`IND`) is in the PDF inventory but not in the Top50 master.
- Valid chunks: 1,100; blank text 0; duplicate Chunk ID 0; page-range error 0.

The previous 663 direct / 229 OCR values came from an earlier extraction diagnostic and are not the current operational page-cache counts.

## Interpretation Boundaries

- The 12,436 KOICA value is a processed record count, not a unique project count. A stable source project ID is absent.
- WDI is a supplementary country context signal. The repository does not prove that all ten stored WDI codes generated `Development_Need_Score`.
- CPS text supports policy review; it does not prove local demand, partner capacity, feasibility or impact.
- Source URLs and collection dates are retained only where present. Missing metadata is displayed as missing, not invented.

Machine-readable hashes and roles are in `data/data_manifest.csv`, `data/cps_document_manifest.csv`, and `artifacts/ai_upgrade/cps_corpus_validation.json`.
