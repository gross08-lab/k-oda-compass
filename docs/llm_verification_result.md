# Optional LLM Runtime Verification

The OpenAI-enhanced generation path is optional. K-ODA Compass remains usable through Local RAG when no API key is configured or an external request fails.

This operational note is not a public KPI report. Evaluator-facing validation values are defined only in `artifacts/screening/canonical_public_kpis.json`.

## Runtime configuration

Set `OPENAI_API_KEY` through an environment variable or Streamlit Secrets. `OPENAI_MODEL` may be used to select an optional configured model. Never commit secret values or generated credential files.

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="<OPTIONAL_MODEL_NAME>"
python3 scripts/verify_llm_call.py
```

The verification script records the actual runtime outcome. A missing key produces an explicit pending result instead of a fabricated external-model success claim.
