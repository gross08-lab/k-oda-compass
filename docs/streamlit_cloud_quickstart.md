# Streamlit Cloud Quickstart

## 1. GitHub repository

Create a public GitHub repository named:

```text
koda-compass-rag
```

Then push this local repository:

```bash
cd /Users/kimjaeyoung/Documents/Codex/2026-07-07/2026-ai/outputs/KODA_Compass_Streamlit_MVP_v2_1_5_RAG
git remote add origin https://github.com/<your-id>/koda-compass-rag.git
git push -u origin main
```

## 2. Streamlit Cloud

1. Go to Streamlit Cloud.
2. Click `Create app`.
3. Select the GitHub repository.
4. Set main file path:

```text
app.py
```

5. Add secrets if LLM mode is needed:

```toml
OPENAI_API_KEY = "..."
OPENAI_MODEL = "gpt-5.2"
```

6. Deploy.

## 3. After deploy

Update these places with the live URL:

- `README.md`
- App `배포` tab input
- Presentation deck QR
- User feedback messages

## 4. Smoke test

Use a clean browser or incognito window.

1. Open live URL.
2. Go to `AI Builder`.
3. Select `CSO 탄자니아 공공행정`.
4. Click `RAG형 AI 사업기획서 생성`.
5. Confirm `CPS PDF`, `KOICA Project`, `WDI`, and `Policy/Risk` citations appear.
6. Go to `심사모드`.
7. Confirm the judging matrix appears.
