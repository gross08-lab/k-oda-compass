# Controlled Generation Experiment Report

## Status

- Result: `NOT_EXECUTED_NO_API_KEY`
- Cases: 10 country-sector cases
- Conditions: `GENERIC`, `RAW_EVIDENCE`, `KODA_CONTROLLED`
- Planned calls: 30
- Executed calls: 0
- Failed calls: 0
- Repeats: 1 planned

## Controlled Design

All three conditions use the same country, sector, user type, scale, keywords, output section order, planned model identifier, timeout, token ceiling, and evaluation code. The only intended difference is the evidence and control layer supplied by the condition prompt.

- `GENERIC`: user conditions only.
- `RAW_EVIDENCE`: the same user conditions plus the same CPS source passage.
- `KODA_CONTROLLED`: the same conditions plus stored Opportunity Score context, structured Evidence Pack, Evidence Class, Citation rules, and A01-A07 assumption separation.

Planned runtime parameters are recorded in `controlled_experiment_summary.json`. Temperature and seed are `null` because the selected Responses API path does not set those parameters in this harness.

## Evaluation

The deterministic evaluator implements Citation coverage, invalid Evidence ID detection, A-ID assumption separation, unsupported numeric-claim screening, and required-section completeness. Citation semantic support remains `REVIEW` when human source comparison is needed.

No output metrics, latency, token usage, cost, or A/B/C improvement values were calculated because no model call was executed. The proposal therefore retains a model-neutral structural comparison and does not claim that the K-ODA control layer improved generation quality.

## Reproduction

```bash
python3 scripts/build_controlled_generation_cases.py
python3 scripts/run_controlled_generation_experiment.py
python3 scripts/evaluate_controlled_outputs.py
```

With no `OPENAI_API_KEY`, the commands create explicit non-execution records instead of synthetic output.
