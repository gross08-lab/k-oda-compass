from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
VIEWS = [
    "개요",
    "순위",
    "프로필",
    "분야 우선검토",
    "AI Builder",
    "근거·재현성",
    "AI·모델 검증",
    "심사용 요약",
    "배포",
]


@pytest.mark.parametrize("view", VIEWS)
def test_each_top_level_view_renders_without_api_key(monkeypatch, view):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    app = AppTest.from_file(str(APP), default_timeout=30)
    app.session_state["active_view"] = view

    app.run()

    assert not app.exception
    assert app.session_state["active_view"] == view


def test_ai_builder_generates_local_rag_output_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    app = AppTest.from_file(str(APP), default_timeout=60)
    app.session_state["active_view"] = "AI Builder"
    app.run()

    generate = next(button for button in app.button if button.label == "RAG형 AI 사업기획서 생성")
    generate.click().run()

    messages = [element.value for element in [*app.info, *app.warning, *app.success]]
    assert not app.exception
    assert any("Local RAG" in message for message in messages)
    assert any("산출물 자동 품질검사" in message for message in messages)
