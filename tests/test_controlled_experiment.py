from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def test_controlled_conditions_keep_identical_user_input() -> None:
    module = load_script("run_controlled_generation_experiment.py")
    case = {
        "country": "르완다",
        "sector": "기술환경에너지",
        "user_type": "CSO/NGO",
        "scale": "소규모 파일럿",
        "keywords": "디지털 공공서비스",
        "opportunity_score": "65.28",
        "rank": "2",
        "expected_document": "RWA.pdf",
        "expected_page": "26",
        "raw_evidence": "검증 원문",
    }
    prompts = []
    for condition, path in module.CONDITIONS.items():
        prompts.append(module.render_prompt(path.read_text(encoding="utf-8"), case, condition))
    for prompt in prompts:
        for value in (case["country"], case["sector"], case["user_type"], case["scale"], case["keywords"]):
            assert value in prompt


def test_deterministic_evaluator_flags_invalid_citations_and_numbers() -> None:
    module = load_script("evaluate_controlled_outputs.py")
    text = "## 문제정의\nCPS 정책은 중요하다 [E99]. 예산 10억원을 투입한다.\n## 목표\n## 주요활동\n## 기대효과\n## 위험\n## 추가조사"
    metrics = module.evaluate_text(text, {"E01"})
    assert metrics["invalid_evidence_ids"] == 1
    assert metrics["unsupported_numeric_claims"] == 1
    assert metrics["output_completeness"] == 1.0


def test_assumption_separation_requires_all_a_ids() -> None:
    module = load_script("evaluate_controlled_outputs.py")
    text = " ".join(f"[A{index:02d}] 잠정 {index}개월" for index in range(1, 8))
    metrics = module.evaluate_text(text, set())
    assert metrics["a01_to_a07_complete"] is True
    assert metrics["assumption_separation"] == 1.0
