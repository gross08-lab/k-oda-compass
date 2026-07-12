# Model Card: K-ODA Compass RAG

## Purpose

K-ODA Compass RAG is an evidence-grounded AI assistant for preliminary ODA planning. It ranks candidate countries, recommends sectors, retrieves public-data evidence, and drafts proposal materials with citations.

## Components

- Score model: weighted decision model combining development need, Korea cooperation base, sector fit, opportunity gap, policy alignment, risk feasibility, and data reliability.
- Retriever: deterministic lexical retrieval is the operating default. Optional local embedding, hybrid, and metadata-filtered hybrid modes rerank CPS chunks and preserve lexical fallback.
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

- The internal retrieval Gold Set covers 10 independently checked CPS pages expanded into 60 query forms; it is not external validation or 60 independent page reviews.
- On the frozen test split, lexical outperformed the optional embedding and hybrid modes, so semantic search is not presented as universally superior.
- Negative metadata-query rejection was 0% in this benchmark; country and sector filters remain required safeguards.
- The upstream raw-data formulas for the seven stored component scores are not fully preserved. Only the stored-component weighted aggregation is VERIFIED end to end.
- Text-layer CPS PDFs are parsed into page-level chunks; image-only PDFs require OCR before full coverage.
- WDI latest-year gaps and policy/risk proxy gaps remain visible in the app.
- Final ODA decisions require official policy review and local validation.
