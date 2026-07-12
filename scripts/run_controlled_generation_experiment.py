from __future__ import annotations

import csv
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONDITIONS = {
    "GENERIC": ROOT / "prompts" / "controlled_experiment" / "generic.txt",
    "RAW_EVIDENCE": ROOT / "prompts" / "controlled_experiment" / "raw_evidence.txt",
    "KODA_CONTROLLED": ROOT / "prompts" / "controlled_experiment" / "koda_controlled.txt",
}
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")
PARAMETERS = {
    "model": MODEL,
    "temperature": None,
    "seed": None,
    "max_output_tokens": 1600,
    "timeout_seconds": 30,
    "repeats": 1,
    "prompt_version": "controlled-generation-v1",
}


def read_cases() -> list[dict[str, str]]:
    with (ROOT / "benchmarks" / "controlled_generation_cases.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def score_summary(case: dict[str, str]) -> str:
    return f"Opportunity Score {case['opportunity_score']}/100, 저장 순위 {case['rank']}/50"


def evidence_pack(case: dict[str, str]) -> str:
    return (
        f"[E01] Source Evidence · CPS PDF · {case['expected_document']} p.{case['expected_page']}\n"
        f"{case['raw_evidence']}"
    )


def render_prompt(template: str, case: dict[str, str], condition: str) -> str:
    values = {
        "COUNTRY": case["country"],
        "SECTOR": case["sector"],
        "USER_TYPE": case["user_type"],
        "SCALE": case["scale"],
        "KEYWORDS": case["keywords"],
        "RAW_EVIDENCE": case["raw_evidence"],
        "SCORE_SUMMARY": score_summary(case),
        "EVIDENCE_PACK": evidence_pack(case),
    }
    prompt = template
    for key, value in values.items():
        prompt = prompt.replace("{{" + key + "}}", value)
    if "{{" in prompt:
        raise ValueError(f"unresolved template placeholder in {condition}")
    return prompt


def call_model(api_key: str, prompt: str) -> tuple[str, dict[str, Any]]:
    from openai import OpenAI

    client = OpenAI(api_key=api_key, timeout=PARAMETERS["timeout_seconds"], max_retries=1)
    started = time.perf_counter()
    response = client.responses.create(
        model=PARAMETERS["model"],
        input=prompt,
        max_output_tokens=PARAMETERS["max_output_tokens"],
    )
    latency_ms = (time.perf_counter() - started) * 1000
    text = getattr(response, "output_text", "") or ""
    usage = getattr(response, "usage", None)
    return text, {
        "latency_ms": round(latency_ms, 3),
        "input_tokens": getattr(usage, "input_tokens", None) if usage else None,
        "output_tokens": getattr(usage, "output_tokens", None) if usage else None,
    }


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    output_dir = ROOT / "artifacts" / "ai_upgrade" / "controlled_experiment_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    errors = []
    executed = 0
    for case in read_cases():
        for condition, path in CONDITIONS.items():
            template = path.read_text(encoding="utf-8")
            prompt = render_prompt(template, case, condition)
            payload: dict[str, Any] = {
                "case_id": case["case_id"],
                "condition": condition,
                "parameters": PARAMETERS,
                "executed_at_utc": datetime.now(timezone.utc).isoformat(),
                "prompt_sha256": __import__("hashlib").sha256(prompt.encode()).hexdigest(),
                "evidence_ids": ["E01"] if condition == "KODA_CONTROLLED" else [],
            }
            if not api_key:
                payload.update({"execution_status": "NOT_EXECUTED_NO_API_KEY", "output_text": ""})
            else:
                try:
                    output_text, usage = call_model(api_key, prompt)
                    if not output_text.strip():
                        raise RuntimeError("empty model response")
                    payload.update({"execution_status": "EXECUTED", "output_text": output_text, **usage})
                    executed += 1
                except Exception as exc:
                    payload.update({"execution_status": "FAILED", "output_text": "", "error_type": type(exc).__name__})
                    errors.append({"case_id": case["case_id"], "condition": condition, "error_type": type(exc).__name__})
            (output_dir / f"{case['case_id']}__{condition}.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

    error_path = ROOT / "artifacts" / "ai_upgrade" / "controlled_experiment_errors.csv"
    with error_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["case_id", "condition", "error_type"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(errors)
    summary = {
        "status": "EXECUTED" if executed else "NOT_EXECUTED_NO_API_KEY",
        "cases": len(read_cases()),
        "conditions": list(CONDITIONS),
        "planned_calls": len(read_cases()) * len(CONDITIONS),
        "executed_calls": executed,
        "failed_calls": len(errors),
        "parameters": PARAMETERS,
        "claim_allowed": False if not executed else None,
        "note": "No generation or metric values are fabricated when API access is absent.",
    }
    (ROOT / "artifacts" / "ai_upgrade" / "controlled_experiment_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
