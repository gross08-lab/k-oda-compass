# CPS OCR Coverage Report

- Generated: 2026-07-10 14:47:06
- Source directory: `/Users/kimjaeyoung/Downloads/CPS(kor)`
- CPS PDFs checked: 27
- Readable text-layer pages: 663/921
- OCR target pages: 258
- Image-only PDFs requiring OCR: COL, GHA, KHM, MMR, MNG, PAK, PRY
- Partial text-layer PDFs: BGD, BOL, ETH, IDN, IND, KGZ, LAO, NPL, PER, PHL, RWA, TZA, UGA, UZB, VNM

## Interpretation

The RAG corpus already uses all pages that expose a readable text layer. Image-only CPS PDFs are explicitly flagged instead of silently treated as missing evidence. Run `scripts/ocr_cps_pdfs.py` with Tesseract Korean OCR installed to regenerate `KODA_cps_pdf_chunks.csv` with OCR-backed chunks.

## Per-PDF Coverage

| Code | Country | Pages | Readable | OCR Target | Ratio | Status |
|---|---|---:|---:|---:|---:|---|
| BGD | 방글라데시 | 35 | 33 | 2 | 94.3% | Partial text layer |
| BOL | 볼리비아 | 27 | 25 | 2 | 92.6% | Partial text layer |
| COL | 콜롬비아 | 32 | 0 | 32 | 0.0% | Image-only - OCR required |
| EGY | 이집트 | 28 | 28 | 0 | 100.0% | Text layer OK |
| ETH | 에티오피아 | 30 | 28 | 2 | 93.3% | Partial text layer |
| GHA | 가나 | 35 | 0 | 35 | 0.0% | Image-only - OCR required |
| IDN | 인도네시아 | 38 | 36 | 2 | 94.7% | Partial text layer |
| IND | 인도 | 33 | 31 | 2 | 93.9% | Partial text layer |
| KGZ | 키르기스스탄 | 33 | 32 | 1 | 97.0% | Partial text layer |
| KHM | 캄보디아 | 31 | 0 | 31 | 0.0% | Image-only - OCR required |
| LAO | 라오스 | 29 | 27 | 2 | 93.1% | Partial text layer |
| LKA | 스리랑카 | 40 | 40 | 0 | 100.0% | Text layer OK |
| MMR | 미얀마 | 35 | 0 | 35 | 0.0% | Image-only - OCR required |
| MNG | 몽골 | 40 | 0 | 40 | 0.0% | Image-only - OCR required |
| NPL | 네팔 | 48 | 47 | 1 | 97.9% | Partial text layer |
| PAK | 파키스탄 | 30 | 0 | 30 | 0.0% | Image-only - OCR required |
| PER | 페루 | 30 | 28 | 2 | 93.3% | Partial text layer |
| PHL | 필리핀 | 34 | 32 | 2 | 94.1% | Partial text layer |
| PRY | 파라과이 | 27 | 0 | 27 | 0.0% | Image-only - OCR required |
| RWA | 르완다 | 47 | 45 | 2 | 95.7% | Partial text layer |
| SEN | 세네갈 | 47 | 47 | 0 | 100.0% | Text layer OK |
| TJK | 타지키스탄 | 37 | 37 | 0 | 100.0% | Text layer OK |
| TZA | 탄자니아 | 30 | 28 | 2 | 93.3% | Partial text layer |
| UGA | 우간다 | 26 | 24 | 2 | 92.3% | Partial text layer |
| UKR | 우크라이나 | 35 | 35 | 0 | 100.0% | Text layer OK |
| UZB | 우즈베키스탄 | 30 | 28 | 2 | 93.3% | Partial text layer |
| VNM | 베트남 | 34 | 32 | 2 | 94.1% | Partial text layer |

## Submission Note

This report is included to make CPS evidence coverage auditable. The app can run from the committed CSV without parsing PDFs at startup, while OCR can be re-run offline when the source PDF set changes.
