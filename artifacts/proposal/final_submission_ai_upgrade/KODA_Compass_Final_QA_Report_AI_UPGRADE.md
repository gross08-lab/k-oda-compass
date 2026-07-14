# K-ODA Compass Final QA Report - 18:00 Submission

## Submission PDF

- File: `KODA_Compass_Proposal_FINAL_SUBMISSION_1800.pdf`
- Size: 2,133,403 bytes
- SHA-256: `f02fe735ef3d7ec0bb3d8aa9ac5f397dfe93422df3f19d788ddd2eb72277d728`
- Pages: 10
- Page size: A4 on all 10 pages
- Render: all pages rendered at 200 dpi
- Blank-page check: 10/10 nonblank
- Visual review: pages 1-10 inspected from the final 200 dpi render; no clipping, overlap, black rendering artifacts, or broken Korean text observed
- Page numbering: 1/10 through 10/10 present

## Links And QR

- Live Demo annotation: `https://k-oda-compass.streamlit.app` - present
- GitHub annotation: `https://github.com/gross08-lab/k-oda-compass` - present
- Page 1 QR payload source and PDF link annotation: `https://k-oda-compass.streamlit.app`
- Page 10 QR payload source and PDF link annotation: `https://github.com/gross08-lab/k-oda-compass`
- Direct QR re-decode from the regenerated image was blocked by the local Vision runtime; QR payload source, visible render and link annotations were verified, but this run does not claim an independent image decode.
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
- Final render contact sheet: `KODA_Compass_Contact_Sheet_1800.png`

## Runtime QA

- Port-bound local Streamlit start: BLOCKED_BY_SANDBOX before app execution
- Streamlit `AppTest` without `OPENAI_API_KEY`: PASS
- Top-level views rendered through `AppTest`: 9/9
- Local RAG Builder button and result generated through `AppTest`: PASS
- Builder automatic quality status: REVIEW, BLOCK 0
- LLM mode without API key: explicit message + Local RAG fallback PASS
- Embedding mode without optional dependency: explicit message + lexical fallback PASS
- No Streamlit runtime exception occurred through all nine view renders and Local RAG generation.
- Browser console and external deployment behavior were not re-certified in this sandbox run.

## Model And Retrieval QA

- Retrieval Gold Set: 120 verified query forms from 27 independently checked CPS PDF pages
- Frozen split: dev 29 / test 91
- Test Recall@5: lexical 1.000, embedding 0.268, hybrid 0.963, filtered hybrid 1.000
- Filtered Hybrid Test MRR: 0.716; nDCG@5: 0.787
- Operational benchmark mode: `hybrid_filtered`; deterministic lexical fallback retained
- Negative metadata-query rejection: 1/9; disclosed as a limitation
- Embedding index: 1,100 chunks, 1,569,151 bytes, source hash checked
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
- `python3 -m pytest -q`: 54 passed
- `git diff --check`: PASS at final review

## Residual Limits

- CPS page cache covers 901/921 pages: 652 direct extraction and 249 OCR-backed; 20 pages remain unsearchable.
- The seven component-score upstream formulas were not preserved and were not reconstructed by fitting.
- The internal Gold Set is not external expert validation.
- External-user pilot and independent ODA expert review remain future work.
