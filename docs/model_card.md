# Model Card: K-ODA Compass RAG

## Purpose

K-ODA Compass RAG is an evidence-grounded AI assistant for preliminary ODA planning. It ranks candidate countries, recommends sectors, retrieves public-data evidence, and drafts proposal materials with citations.

## Components

- Score model: weighted decision model combining development need, Korea cooperation base, sector fit, opportunity gap, policy alignment, risk feasibility, and data reliability.
- Retriever: local token-based RAG search over KOICA projects, WDI indicators, CPS PDF chunks, sector portfolios, score rows, and policy/risk proxy rows.
- Generator: local citation-preserving proposal generator.
- Optional LLM: OpenAI Responses API, activated only when `OPENAI_API_KEY` is configured.

## Grounding Rules

- Retrieved evidence receives stable IDs such as `[E01]`.
- Proposal text must cite evidence IDs for country, sector, CPS, WDI, policy, risk, and KOICA project claims.
- Policy/risk values are treated as proxy signals, not final feasibility decisions.
- The system avoids final project-selection claims before CPS, local demand, partner, and budget validation.

## Evaluation Signals

- Score reproducibility: v2.1 score formula matches stored score within rounding tolerance.
- Evidence coverage: KOICA, WDI, score, policy/risk, and sector portfolio evidence are retrieved separately.
- CPS coverage: extracted CPS PDF chunks and country coverage are reported in the AI validation tab.
- Sensitivity analysis: selected score components are perturbed to show rank stability.
- Hallucination control: LLM prompt is restricted to Evidence Pack content.

## Limitations

- Current RAG retrieval is lexical and deterministic, not embedding-based.
- Text-layer CPS PDFs are parsed into page-level chunks; image-only PDFs require OCR before full coverage.
- WDI latest-year gaps and policy/risk proxy gaps remain visible in the app.
- Final ODA decisions require official policy review and local validation.
