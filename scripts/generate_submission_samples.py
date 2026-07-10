from __future__ import annotations

import sys
import types
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


SCENARIOS = [
    ("tanzania_public_admin_cso", "탄자니아", "공공행정", "CSO/NGO", "소규모 파일럿", "디지털 행정, 현지 역량강화, 성과관리"),
    ("vietnam_digital_government_local", "베트남", "공공행정", "지자체", "민관협력형", "디지털정부, 지방행정, 공무원 교육"),
    ("rwanda_ict_energy_company", "르완다", "기술환경에너지", "기업/스타트업", "중형 확장사업", "ICT, 에너지 접근성, 민관협력"),
]


def write_bytes(path: Path, data: bytes | None) -> None:
    if data:
        path.write_bytes(data)


def main() -> None:
    out_dir = Path("sample_outputs")
    out_dir.mkdir(exist_ok=True)

    data = app.load_all_data()
    corpus = app.build_rag_corpus(
        data["master"],
        data["wdi"],
        data["projects"],
        data["policy_risk"],
        data["sector_summary"],
        data["cps_pdf"],
    )

    index_lines = ["# K-ODA Compass Sample Outputs", ""]
    for slug, country, sector, user_type, scale, keywords in SCENARIOS:
        row = app.get_country_row(data["master"], country)
        docs = app.retrieve_rag_evidence(corpus, country, sector, keywords, row, top_k=16)
        proposal = app.build_rag_markdown_proposal(country, sector, user_type, scale, keywords, row, docs, data["weights"])
        brief = app.build_policy_brief(country, sector, row, docs)
        evidence_pack = app.build_rag_evidence_pack(country, sector, keywords, docs)

        proposal_path = out_dir / f"{slug}_proposal.md"
        brief_path = out_dir / f"{slug}_brief.md"
        evidence_path = out_dir / f"{slug}_evidence_pack.md"
        proposal_path.write_text(proposal, encoding="utf-8")
        brief_path.write_text(brief, encoding="utf-8")
        evidence_path.write_text(evidence_pack, encoding="utf-8")
        write_bytes(out_dir / f"{slug}_proposal.pdf", app.markdown_to_pdf_bytes(f"KODA {country} {sector} Proposal", proposal))
        write_bytes(out_dir / f"{slug}_brief.pdf", app.markdown_to_pdf_bytes(f"KODA {country} {sector} Policy Brief", brief))

        index_lines.extend([
            f"## {country} - {sector}",
            f"- User: {user_type}",
            f"- Scale: {scale}",
            f"- Keywords: {keywords}",
            f"- Proposal: `{proposal_path.name}`",
            f"- Brief: `{brief_path.name}`",
            f"- Evidence Pack: `{evidence_path.name}`",
            "",
        ])

    (out_dir / "README.md").write_text("\n".join(index_lines), encoding="utf-8")
    print(f"Generated {len(SCENARIOS)} scenarios in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
