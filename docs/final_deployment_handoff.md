# Final Deployment Handoff

## What Is Already Ready

- Streamlit entrypoint: `app.py`
- Committed data bundle: KOICA, WDI, policy/risk proxy, CPS PDF chunks
- RAG Builder: citation-first local RAG plus optional OpenAI Responses API mode
- Output artifacts: proposal, policy brief, evidence pack, service-style case studies
- QR generator: app `배포·QR 센터` and `scripts/make_qr.py`

## Required External Access

Actual Streamlit Cloud deployment cannot be completed from this local package alone. It requires:

1. GitHub repository URL or GitHub login access
2. Streamlit Cloud login access
3. Optional `OPENAI_API_KEY` for live LLM mode

## Push to GitHub

```bash
git remote add origin https://github.com/gross08-lab/k-oda-compass.git
git push -u origin main
```

If a remote already exists:

```bash
git remote set-url origin https://github.com/gross08-lab/k-oda-compass.git
git push -u origin main
```

## Streamlit Cloud Setup

1. Create a new Streamlit app from the GitHub repository.
2. Set the main file path to `app.py`.
3. Set Python dependencies from `requirements.txt`.
4. Add secrets:

```toml
OPENAI_API_KEY = "..."
OPENAI_MODEL = "gpt-5.2"
```

5. Deploy.
6. Copy the Streamlit URL.
7. Replace the placeholders in `README.md`, the app `배포` tab, and presentation materials.

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
python3 scripts/cps_ocr_coverage.py --input "/Users/kimjaeyoung/Downloads/CPS(kor)"
python3 scripts/verify_llm_call.py
python3 scripts/generate_submission_samples.py
python3 scripts/generate_case_study_pdfs.py
```

`scripts/verify_llm_call.py` writes `docs/llm_verification_result.md`. Without `OPENAI_API_KEY`, it writes a pending report instead of making a network call.
