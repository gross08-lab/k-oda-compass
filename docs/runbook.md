# Validation Runbook

## Core QA

```bash
python3 -m py_compile app.py
PYTHONPATH=. pytest -q
git diff --check
```

## CPS Corpus

The PDF/OCR scripts require pypdf, pdfplumber and Poppler. Reuse the verified page cache when OCR need not be rerun:

```bash
python3 scripts/ocr_cps_pdfs.py --input data/cps_pdfs --page-cache data/cps_page_text.csv --reuse-page-cache --max-chars 1024 --overlap 120
python3 scripts/cps_ocr_coverage.py --input data/cps_pdfs --page-cache data/cps_page_text.csv
python3 scripts/validate_cps_corpus.py
```

Run `validate_cps_corpus.py` twice and compare `deterministic_chunk_frame_sha256` in `cps_corpus_validation.json`.

## Retrieval

Install the optional environment from `requirements-ai-upgrade.txt`; model cache files remain untracked.

```bash
PYTHONPATH=. python scripts/verify_retrieval_gold_freeze.py
PYTHONPATH=. python scripts/build_embedding_index.py
PYTHONPATH=. python scripts/run_retrieval_benchmark.py --phase dev
```

Apply only the Dev-selected lexical/embedding weights and phrase bonus to `config/retrieval.yaml`, then run the final Test once:

```bash
PYTHONPATH=. python scripts/run_retrieval_benchmark.py --phase final
```

Do not edit Gold labels, expected IDs or split after the freeze manifest is established.

## Score, Citation and Generation

```bash
PYTHONPATH=. python3 scripts/build_score_lineage_artifacts.py
PYTHONPATH=. python3 scripts/rebuild_scores.py
python3 scripts/audit_citations.py
env -u OPENAI_API_KEY PYTHONPATH=. python3 scripts/run_controlled_generation_experiment.py
PYTHONPATH=. python3 scripts/evaluate_controlled_outputs.py
```

The no-key experiment must remain 0 executed calls. Never write Secrets, `.env` or API keys to the repository.

## App

```bash
env -u OPENAI_API_KEY streamlit run app.py
```

Confirm all nine segmented views, Local RAG fallback, Proposal/Brief/Evidence Pack and both PDFs. Validation JSON files are loaded only in the audit view and use bounded Streamlit caches.
