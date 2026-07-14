# Final Deployment Handoff

## What Is Already Ready

- Streamlit entrypoint: `app.py`
- Committed data bundle: KOICA, WDI, policy/risk proxy, CPS PDF chunks
- RAG Builder: citation-first local RAG plus optional OpenAI Responses API mode
- Output artifacts: proposal, policy brief, evidence pack, service-style case studies
- QR generator: app `배포·QR 센터` and `scripts/make_qr.py`

## Live Deployment

The public deployment is available at:

- GitHub: `https://github.com/gross08-lab/k-oda-compass`
- Streamlit: `https://k-oda-compass.streamlit.app`
- Optional `OPENAI_API_KEY` for live LLM mode

## Update GitHub

```bash
git remote set-url origin https://github.com/gross08-lab/k-oda-compass.git
git push -u origin main
```

## Streamlit Cloud Setup

1. Open the existing Streamlit app connected to the public GitHub repository.
2. Confirm the main file path is `app.py`.
3. Set Python dependencies from `requirements.txt`.
4. Add secrets:

```toml
OPENAI_API_KEY = "..."
OPENAI_MODEL = "<OPTIONAL_MODEL_NAME>"
```

5. Deploy or reboot the existing app.
6. Confirm `https://k-oda-compass.streamlit.app` opens successfully.

## QR Update

After the URLs are known:

```bash
python3 scripts/make_qr.py --url "https://k-oda-compass.streamlit.app" --output koda_demo_qr.png
python3 scripts/make_qr.py --url "https://github.com/gross08-lab/k-oda-compass" --output koda_github_qr.png
```

The app also generates downloadable QR codes from the `배포·QR 센터` tab.

## Final Verification

```bash
pytest
python3 scripts/cps_ocr_coverage.py --input "<CPS_PDF_DIRECTORY>"
python3 scripts/verify_llm_call.py
python3 scripts/generate_submission_samples.py
python3 scripts/generate_case_study_pdfs.py
```

`scripts/verify_llm_call.py` writes `docs/llm_verification_result.md`. Without `OPENAI_API_KEY`, it writes a pending report instead of making a network call.
