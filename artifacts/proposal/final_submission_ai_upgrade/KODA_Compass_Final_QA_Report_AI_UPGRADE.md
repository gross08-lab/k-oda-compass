# K-ODA Compass Final QA Report - AI Upgrade

## Submission PDF

- File: `KODA_Compass_Proposal_FINAL_SUBMISSION_AI_UPGRADE.pdf`
- Size: 7,714,262 bytes
- Pages: 10
- Page size: A4 on all 10 pages
- Render: all pages rendered at 200 dpi
- Blank-page check: 10/10 nonblank
- Visual review: pages 1, 4, 5, 6, 7, 8, 9, and 10 inspected; no clipping, overlap, or broken Korean text observed
- Page numbering: 1/10 through 10/10 present

## Links And QR

- Live Demo annotation: `https://k-oda-compass.streamlit.app` - present
- GitHub annotation: `https://github.com/gross08-lab/k-oda-compass` - present
- Page 1 QR decoded from the final 200 dpi rendered image: `https://k-oda-compass.streamlit.app`
- Page 10 QR decoded from the final 200 dpi rendered image: `https://github.com/gross08-lab/k-oda-compass`
- QR quiet zones remained visible in the inspected crops.

## Typography

- Korean text render: PASS
- Embedded font resource inspection: subset NotoSansCJKkr and NanumGothic font programs are present.
- Generic Helvetica and Times resources do not carry Korean content.

## Automated Content QA

- Forbidden proposal phrases: 0 hits
- API key or secret pattern in PDF: 0 hits
- Local absolute path in PDF: 0 hits
- Live Demo and GitHub URL placeholders: 0 hits
- Automated details: `qa_automated_results.json`

## Runtime QA

- Local Streamlit start without `OPENAI_API_KEY`: PASS
- Top-level views opened: 9/9
- Local RAG Builder result generated: PASS
- Builder automatic quality status: REVIEW, BLOCK 0
- LLM mode without API key: explicit message + Local RAG fallback PASS
- Embedding mode without optional dependency: explicit message + lexical fallback PASS
- App process remained alive through all view changes and generation attempts.
- Browser console errors: 0; existing chart-library warnings were nonfatal.

## Model And Retrieval QA

- Retrieval Gold Set: 60 verified query forms from 10 independently checked CPS PDF pages
- Frozen split: dev 21 / test 39
- Test Recall@5: lexical 1.00, embedding 0.52, hybrid 0.80, filtered hybrid 0.96
- Operating default: lexical
- Negative metadata-query rejection: 0%; disclosed as a limitation
- Embedding index: 806 chunks, 1,150,060 bytes, source hash checked
- Model cache and ONNX weights: excluded from Git

## Score And Generation QA

- Stored-component Opportunity Score reproduction: 50/50
- Rank reproduction: 50/50
- Maximum absolute error: 0.005
- Raw-to-component full reproduction: 0 countries
- Lineage: VERIFIED 1, PARTIAL 6, UNRESOLVED 1
- Controlled A/B/C harness: implemented for 10 cases x 3 conditions
- Actual controlled generation calls: 0 (`OPENAI_API_KEY` absent)
- No A/B/C performance, latency, cost, or quality-improvement values claimed.

## Tests

- `python3 -m py_compile`: PASS
- `python3 -m pytest -q`: 38 passed
- `git diff --check`: PASS at final review

## Residual Limits

- Seven image-centered CPS PDFs still require OCR before full search coverage.
- The seven component-score upstream formulas were not preserved and were not reconstructed by fitting.
- The internal Gold Set is not external expert validation.
- External-user pilot and independent ODA expert review remain future work.
