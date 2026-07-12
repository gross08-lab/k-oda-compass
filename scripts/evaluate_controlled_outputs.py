from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_SECTIONS = ("문제정의", "목표", "주요활동", "기대효과", "위험", "추가조사")
FACT_TERMS = ("CPS", "국가협력전략", "KOICA", "WDI", "정책", "사업", "지표", "점수")


def sentence_units(text: str) -> list[str]:
    return [unit.strip() for unit in re.split(r"(?<=[.!?다요])\s+|\n+", text) if unit.strip()]


def unsupported_numeric_claims(text: str) -> list[str]:
    failures = []
    for unit in sentence_units(text):
        if not re.search(r"\d", unit):
            continue
        if re.search(r"\[(?:E|A)\d{2}\]", unit):
            continue
        failures.append(unit)
    return failures


def evaluate_text(text: str, evidence_ids: set[str]) -> dict[str, Any]:
    citations = re.findall(r"\[(E\d{2})\]", text)
    assumption_ids = set(re.findall(r"\[(A\d{2})\]", text))
    factual_units = [unit for unit in sentence_units(text) if any(term in unit for term in FACT_TERMS)]
    cited_factual = [unit for unit in factual_units if re.search(r"\[E\d{2}\]", unit)]
    unknown = sorted(set(citations) - evidence_ids)
    required = {section: section in text for section in REQUIRED_SECTIONS}
    design_numbers = [unit for unit in sentence_units(text) if re.search(r"(?:개월|명|억원|KPI|파트너)", unit)]
    separated = [unit for unit in design_numbers if re.search(r"\[A\d{2}\]", unit)]
    semantic_review = sum(
        1 for unit in cited_factual
        if "CPS" in unit and not re.search(r"\[E\d{2}\]", unit)
    )
    return {
        "citation_needed_claims": len(factual_units),
        "cited_factual_claims": len(cited_factual),
        "citation_coverage": len(cited_factual) / len(factual_units) if factual_units else None,
        "citation_count": len(citations),
        "invalid_evidence_ids": len(unknown),
        "invalid_evidence_id_list": "|".join(unknown),
        "semantic_support_status": "REVIEW" if semantic_review or citations else "INFO",
        "design_numeric_claims": len(design_numbers),
        "a_id_separated_claims": len(separated),
        "assumption_separation": len(separated) / len(design_numbers) if design_numbers else None,
        "a01_to_a07_complete": all(f"A{index:02d}" in assumption_ids for index in range(1, 8)),
        "unsupported_numeric_claims": len(unsupported_numeric_claims(text)),
        "required_sections_present": sum(required.values()),
        "required_sections_total": len(required),
        "output_completeness": sum(required.values()) / len(required),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=ROOT / "artifacts" / "ai_upgrade" / "controlled_experiment_outputs")
    args = parser.parse_args()
    rows = []
    for path in sorted(args.input_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("execution_status") != "EXECUTED":
            rows.append(
                {
                    "case_id": payload.get("case_id"),
                    "condition": payload.get("condition"),
                    "execution_status": payload.get("execution_status"),
                    "evaluation_status": "NOT_EVALUATED",
                }
            )
            continue
        metrics = evaluate_text(payload.get("output_text", ""), set(payload.get("evidence_ids", [])))
        rows.append(
            {
                "case_id": payload.get("case_id"),
                "condition": payload.get("condition"),
                "execution_status": "EXECUTED",
                "evaluation_status": "DETERMINISTIC_COMPLETE_WITH_SEMANTIC_REVIEW",
                **metrics,
            }
        )
    out = ROOT / "artifacts" / "ai_upgrade" / "controlled_experiment_results.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row}) if rows else ["case_id", "condition", "execution_status", "evaluation_status"]
    with out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"evaluated_rows={sum(row.get('execution_status') == 'EXECUTED' for row in rows)} total={len(rows)}")


if __name__ == "__main__":
    main()
