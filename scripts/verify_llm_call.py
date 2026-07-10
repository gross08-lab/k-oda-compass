from __future__ import annotations

import argparse
import os
import re
import sys
import types
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if "streamlit" not in sys.modules:
    streamlit_stub = types.ModuleType("streamlit")

    def cache_data(*args, **kwargs):
        if args and callable(args[0]):
            return args[0]

        def decorator(fn):
            return fn

        return decorator

    streamlit_stub.cache_data = cache_data
    streamlit_stub.set_page_config = lambda *args, **kwargs: None
    streamlit_stub.secrets = {}
    sys.modules["streamlit"] = streamlit_stub

if "plotly" not in sys.modules:
    plotly_stub = types.ModuleType("plotly")
    express_stub = types.ModuleType("plotly.express")
    graph_objects_stub = types.ModuleType("plotly.graph_objects")
    sys.modules["plotly"] = plotly_stub
    sys.modules["plotly.express"] = express_stub
    sys.modules["plotly.graph_objects"] = graph_objects_stub

import app


DEFAULT_OUTPUT = Path("docs/llm_verification_result.md")


def write_report(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify the actual OpenAI LLM path used by K-ODA Compass.")
    parser.add_argument("--country", default="탄자니아")
    parser.add_argument("--sector", default="공공행정")
    parser.add_argument("--user-type", default="CSO/NGO")
    parser.add_argument("--scale", default="소규모 파일럿")
    parser.add_argument("--keywords", default="디지털 행정, 현지 역량강화, 성과관리")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    output = Path(args.output)
    api_key_present = bool(os.environ.get("OPENAI_API_KEY"))
    model = os.environ.get("OPENAI_MODEL", "gpt-5.2")

    data = app.load_all_data()
    row = app.get_country_row(data["master"], args.country)
    corpus = app.build_rag_corpus(
        data["master"],
        data["wdi"],
        data["projects"],
        data["policy_risk"],
        data["sector_summary"],
        data["cps_pdf"],
    )
    docs = app.retrieve_rag_evidence(corpus, args.country, args.sector, args.keywords, row, top_k=16)
    prompt = app.build_rag_prompt(args.country, args.sector, args.user_type, args.scale, args.keywords, row, docs, data["weights"])
    evidence_ids = docs["Citation_ID"].tolist()

    if not api_key_present:
        write_report(
            output,
            [
                "# LLM Verification Result",
                "",
                f"- Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "- Status: pending_api_key",
                f"- Intended model: {model}",
                "- OPENAI_API_KEY present: no",
                f"- Evidence IDs prepared: {', '.join(evidence_ids)}",
                f"- Prompt characters: {len(prompt)}",
                "",
                "## Interpretation",
                "",
                "The app's local RAG path is fully runnable, but an actual OpenAI Responses API call was not executed because no API key is available in this environment.",
                "",
                "## How to Produce the Final Capture",
                "",
                "```bash",
                "export OPENAI_API_KEY=\"...\"",
                "export OPENAI_MODEL=\"gpt-5.2\"",
                "python3 scripts/verify_llm_call.py",
                "```",
                "",
                "A successful run overwrites this file with model, citation count, response excerpt, and citation-presence checks.",
            ],
        )
        print(f"wrote pending verification report: {output.resolve()}")
        return

    text, status = app.call_openai_llm(prompt)
    citation_hits = sorted(set(re.findall(r"\[E\d{2}\]", text or "")))
    verified = bool(text) and bool(citation_hits)
    excerpt = (text or "").replace("\r", " ").strip()[:1800]
    write_report(
        output,
        [
            "# LLM Verification Result",
            "",
            f"- Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- Status: {'verified_actual_llm_call' if verified else 'llm_call_completed_but_citation_check_failed'}",
            f"- API status: {status}",
            f"- Model: {model}",
            "- OPENAI_API_KEY present: yes",
            f"- Evidence IDs prepared: {', '.join(evidence_ids)}",
            f"- Citation IDs found in LLM output: {', '.join(citation_hits) if citation_hits else 'None'}",
            f"- Prompt characters: {len(prompt)}",
            f"- Output characters: {len(text or '')}",
            "",
            "## Output Excerpt",
            "",
            excerpt or "No output text returned.",
        ],
    )
    print(f"wrote LLM verification report: {output.resolve()}")


if __name__ == "__main__":
    main()
