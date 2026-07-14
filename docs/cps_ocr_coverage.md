# CPS OCR Coverage Report

- Generated: 2026-07-14 12:45:37
- Source directory: `cps_pdfs`
- CPS PDFs checked: 27
- Directly extracted searchable pages: 652/921
- pypdf-only OCR target diagnostic: 278
- OCR-completed searchable pages: 249
- Total searchable pages: 901
- Searchable countries: 27/27
- Image-only PDFs requiring OCR: COL, GHA, KHM, MMR, MNG, PAK, PRY
- Partial text-layer PDFs: BGD, BOL, EGY, ETH, IDN, IND, KGZ, LAO, LKA, NPL, PER, PHL, RWA, SEN, TJK, TZA, UGA, UKR, UZB, VNM

## Interpretation

The RAG corpus already uses all pages that expose a readable text layer. Image-only CPS PDFs are explicitly flagged instead of silently treated as missing evidence. Run `scripts/ocr_cps_pdfs.py --engine auto` to use Tesseract when available or macOS Vision OCR on supported systems.

## Per-PDF Coverage

| Code | Country | Pages | Direct extract | OCR target diagnostic | OCR complete | Search pages | Chunks | Status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| BGD | 방글라데시 | 35 | 33 | 3 | 2 | 35 | 43 | Searchable |
| BOL | 볼리비아 | 27 | 24 | 3 | 1 | 25 | 35 | Searchable |
| COL | 콜롬비아 | 32 | 0 | 32 | 32 | 32 | 33 | Searchable |
| EGY | 이집트 | 28 | 27 | 1 | 1 | 28 | 33 | Searchable |
| ETH | 에티오피아 | 30 | 27 | 3 | 1 | 28 | 35 | Searchable |
| GHA | 가나 | 35 | 0 | 35 | 35 | 35 | 42 | Searchable |
| IDN | 인도네시아 | 38 | 37 | 3 | 1 | 38 | 43 | Searchable |
| IND | 인도 | 33 | 32 | 3 | 1 | 33 | 42 | Searchable |
| KGZ | 키르기스스탄 | 33 | 32 | 2 | 1 | 33 | 42 | Searchable |
| KHM | 캄보디아 | 31 | 0 | 31 | 31 | 31 | 37 | Searchable |
| LAO | 라오스 | 29 | 26 | 3 | 1 | 27 | 34 | Searchable |
| LKA | 스리랑카 | 40 | 39 | 1 | 1 | 40 | 49 | Searchable |
| MMR | 미얀마 | 35 | 0 | 35 | 35 | 35 | 40 | Searchable |
| MNG | 몽골 | 40 | 0 | 40 | 40 | 40 | 44 | Searchable |
| NPL | 네팔 | 48 | 47 | 2 | 1 | 48 | 56 | Searchable |
| PAK | 파키스탄 | 30 | 0 | 30 | 30 | 30 | 35 | Searchable |
| PER | 페루 | 30 | 27 | 3 | 1 | 28 | 36 | Searchable |
| PHL | 필리핀 | 34 | 31 | 3 | 1 | 32 | 45 | Searchable |
| PRY | 파라과이 | 27 | 0 | 27 | 25 | 25 | 29 | Searchable |
| RWA | 르완다 | 47 | 46 | 3 | 1 | 47 | 57 | Searchable |
| SEN | 세네갈 | 47 | 46 | 1 | 1 | 47 | 58 | Searchable |
| TJK | 타지키스탄 | 37 | 36 | 1 | 1 | 37 | 45 | Searchable |
| TZA | 탄자니아 | 30 | 27 | 3 | 1 | 28 | 36 | Searchable |
| UGA | 우간다 | 26 | 23 | 3 | 1 | 24 | 32 | Searchable |
| UKR | 우크라이나 | 35 | 34 | 1 | 1 | 35 | 43 | Searchable |
| UZB | 우즈베키스탄 | 30 | 27 | 3 | 1 | 28 | 34 | Searchable |
| VNM | 베트남 | 34 | 31 | 3 | 1 | 32 | 42 | Searchable |

## Submission Note

This report is included to make CPS evidence coverage auditable. The app can run from the committed CSV without parsing PDFs at startup, while OCR can be re-run offline when the source PDF set changes.
