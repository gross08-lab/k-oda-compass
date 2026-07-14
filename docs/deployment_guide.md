# Deployment Guide

## GitHub

1. Use the repository `k-oda-compass`.
2. Commit every file in this folder.
3. Push to GitHub.

```bash
git init
git add .
git commit -m "Add K-ODA Compass RAG submission"
git branch -M main
git remote add origin https://github.com/gross08-lab/k-oda-compass.git
git push -u origin main
```

## Streamlit Cloud

1. Open Streamlit Cloud.
2. Select the GitHub repository.
3. Set main file path to `app.py`.
4. Add secrets:

```toml
OPENAI_API_KEY = "..."
OPENAI_MODEL = "<OPTIONAL_MODEL_NAME>"
```

5. Deploy and copy the live URL.
6. Paste GitHub and Streamlit URLs into the app's `배포` tab.
7. Download QR images for the presentation deck.

## CPS PDF Refresh

If CPS PDFs are updated, regenerate the chunk CSV before deployment:

```bash
python3 scripts/ingest_cps_pdfs.py --input "<CPS_PDF_DIRECTORY>" --output KODA_cps_pdf_chunks.csv
```

Audit OCR coverage:

```bash
python3 scripts/cps_ocr_coverage.py --input "<CPS_PDF_DIRECTORY>"
```

If Tesseract Korean OCR is installed, regenerate chunks with OCR fallback:

```bash
python3 scripts/ocr_cps_pdfs.py --input "<CPS_PDF_DIRECTORY>" --output KODA_cps_pdf_chunks.csv
```

Commit the regenerated `KODA_cps_pdf_chunks.csv` so Streamlit Cloud can run without reparsing PDF files at startup.

## LLM Verification

Before final submission, run:

```bash
python3 scripts/verify_llm_call.py
```

With `OPENAI_API_KEY`, this writes an actual Responses API verification capture to `docs/llm_verification_result.md`. Without the key, it records a pending status and the exact command needed to complete the capture.

## Local Docker

```bash
docker build -t k-oda-compass .
docker run -p 8501:8501 -e OPENAI_API_KEY="$OPENAI_API_KEY" k-oda-compass
```

## Recommended Presentation URL Set

- Live app URL
- GitHub repository URL
- QR image for live app
- QR image for repository
