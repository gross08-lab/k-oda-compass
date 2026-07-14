# RAG and Citation Architecture

## Public validation scope

Evaluator-facing KPI values are defined only in `artifacts/screening/canonical_public_kpis.json`. Submission-time frozen validation and post-submission engineering diagnostics use different evaluation scopes. Internal diagnostic values are not Live Demo KPIs and are not restated in this document.

## CPS pipeline

1. Preserve each original CPS PDF and its SHA-256 value.
2. Select the better direct text from the available PDF parsers.
3. Apply OCR to noisy or image-based pages.
4. Exclude pages that remain empty or unusable.
5. Chunk each searchable page with bounded overlap.
6. Assign deterministic IDs and retain the PDF name, page, extraction method and source hash.

Current corpus inventory and coverage values are read from the canonical public manifest rather than independently declared here.

## Retrieval

The metadata-filtered ranker uses BM25 term weighting, query-term coverage, phrase-frequency signals, source metadata and deterministic Chunk-ID tie-breaking. English ODA terms are expanded through a general domain dictionary. There are no query-ID, Gold Chunk-ID, country-page or answer-text exceptions.

Optional embedding and hybrid modes normalize scores within the filtered candidate set. The lightweight lexical path remains available when an optional model cannot load.

## Evidence and Citation

Builder outputs share one structured result containing Evidence objects, assumptions and generated text. Evidence classes distinguish source material, supplementary sources, derived evidence, model output and AI design assumptions.

Citation IDs resolve against the same Evidence Pack used by Proposal and Brief. CPS evidence retains document and page metadata. Session-level structural checks do not constitute an external factual-accuracy certification; source-page and field verification remain part of responsible use.
