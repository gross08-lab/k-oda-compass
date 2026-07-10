from __future__ import annotations

import sys
import types
from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd


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

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

import app


SCENARIOS = [
    {
        "slug": "tanzania_public_admin_cso",
        "country": "탄자니아",
        "sector": "공공행정",
        "user_type": "CSO/NGO",
        "scale": "소규모 파일럿",
        "keywords": "디지털 행정, 현지 역량강화, 성과관리",
        "persona": "국제개발 CSO 기획팀이 KOICA 공모형 사업 초안을 빠르게 만들고 내부 심사 근거를 확보하는 상황",
        "decision": "공공행정 파일럿을 우선 검토하되, 실행 리스크는 현지 파트너 공동운영과 성과지표 검증으로 조정",
    },
    {
        "slug": "vietnam_digital_government_local",
        "country": "베트남",
        "sector": "공공행정",
        "user_type": "지자체",
        "scale": "민관협력형",
        "keywords": "디지털정부, 지방행정, 공무원 교육",
        "persona": "국내 지자체 국제협력 담당자가 디지털정부 교류사업 후보국을 비교하고 제안서 근거를 정리하는 상황",
        "decision": "기존 협력기반과 디지털 행정 수요를 연결해 지방행정 역량강화형 협력 모델을 검토",
    },
    {
        "slug": "rwanda_ict_energy_company",
        "country": "르완다",
        "sector": "기술환경에너지",
        "user_type": "기업/스타트업",
        "scale": "중형 확장사업",
        "keywords": "ICT, 에너지 접근성, 민관협력",
        "persona": "개발협력 진출을 준비하는 기업이 국가별 수요와 실행가능성을 보고 민관협력 사업 파이프라인을 설계하는 상황",
        "decision": "ICT와 에너지 접근성 신호를 묶어 민관협력형 실증사업을 검토하되, 재원조달과 운영주체를 단계적으로 검증",
    },
]


def register_fonts() -> tuple[str, str]:
    font_candidates = [
        Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
        Path("/Library/Fonts/Arial Unicode.ttf"),
    ]
    for font_path in font_candidates:
        if font_path.exists():
            pdfmetrics.registerFont(TTFont("KodaKorean", str(font_path)))
            return "KodaKorean", "KodaKorean"
    return "Helvetica-Bold", "Helvetica"


FONT_BOLD, FONT_BODY = register_fonts()


def fmt(value, digits: int = 1) -> str:
    return app.fmt_number(value, digits)


def p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(str(text)).replace("\n", "<br/>"), style)


def heading(text: str, styles: dict[str, ParagraphStyle]) -> list:
    return [Spacer(1, 5), p(text, styles["Section"]), Spacer(1, 4)]


def make_table(data: list[list[str]], widths: list[float], styles: dict[str, ParagraphStyle], header: bool = True) -> Table:
    rows = [[p(cell, styles["TableHeader" if header and r == 0 else "TableBody"]) for cell in row] for r, row in enumerate(data)]
    table = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D5DEE8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        style.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#173A5E")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ]
        )
    table.setStyle(TableStyle(style))
    return table


def bullet_lines(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def top_docs(docs: pd.DataFrame, source_type: str, n: int = 3) -> list[str]:
    subset = docs.loc[docs["Source_Type"] == source_type].head(n)
    return [f"[{r['Citation_ID']}] {r['Title']} - {r['Citation']}" for _, r in subset.iterrows()]


def case_markdown(s: dict, row: pd.Series, docs: pd.DataFrame, contribution: pd.DataFrame) -> str:
    evidence = top_docs(docs, "CPS PDF", 3) + top_docs(docs, "WDI", 3) + top_docs(docs, "KOICA Project", 3)
    roadmap = [
        "0-1개월: 후보국 프로필, CPS 원문, KOICA/WDI 근거팩 검토",
        "1-2개월: 현지 파트너 인터뷰와 KPI baseline 수집",
        "3-6개월: 파일럿 운영, 데이터 품질점검, 성과 대시보드 구축",
        "6-12개월: 확장 제안서, 예산안, 파트너십 구조 확정",
    ]
    controls = [
        "점수모델은 개발수요만 보지 않고 정책정합성, 실행가능성, 데이터 신뢰도를 함께 반영",
        "생성형 AI 문장은 Evidence Pack ID를 남겨 심사자가 원자료 근거를 역추적 가능",
        "CPS OCR 커버리지 리포트로 원문 근거의 추출 가능 범위와 보강 대상을 분리",
    ]
    contrib_lines = [
        f"{r['구성요소']}: 원점수 {fmt(r['원점수'])}, 가중기여 {fmt(r['기여점수'])}"
        for _, r in contribution.head(4).iterrows()
    ]
    return f"""# K-ODA Compass Case Study: {s['country']} {s['sector']}

## Service Positioning
데이터 기반 공공투자 우선순위 산출 및 리스크 조정 의사결정 모델

## User Scenario
{s['persona']}

## Decision
{s['decision']}

## Score Snapshot
- Rank: {app.fmt_int(row.get('Rank_V21'))}
- Opportunity Score: {fmt(row.get('K_ODA_Opportunity_Score_V21'))}/100
- Candidate Type: {app.display_candidate_type(row.get('Candidate_Type_V21'))}
- Recommended Service Angle: {app.safe_text(row.get('Recommended_Service_Angle_V2'))}

## Score Decomposition
{bullet_lines(contrib_lines)}

## Workflow
Raw public data -> risk-adjusted country score -> RAG evidence pack -> AI Builder proposal -> PDF/brief export -> partner validation

## Evidence Highlights
{bullet_lines(evidence)}

## Roadmap
{bullet_lines(roadmap)}

## Risk Controls
{bullet_lines(controls)}
"""


def draw_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(FONT_BODY, 8)
    canvas.setFillColor(colors.HexColor("#6B7280"))
    canvas.drawString(18 * mm, 12 * mm, "K-ODA Compass RAG | Evidence-grounded ODA decision support")
    canvas.drawRightString(192 * mm, 12 * mm, f"p. {doc.page}")
    canvas.restoreState()


def build_pdf(path: Path, s: dict, row: pd.Series, docs: pd.DataFrame, contribution: pd.DataFrame) -> None:
    base = getSampleStyleSheet()
    styles = {
        "Title": ParagraphStyle(
            "KodaTitle",
            parent=base["Title"],
            fontName=FONT_BOLD,
            fontSize=19,
            leading=24,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#173A5E"),
            spaceAfter=7,
        ),
        "Subtitle": ParagraphStyle(
            "KodaSubtitle",
            parent=base["BodyText"],
            fontName=FONT_BODY,
            fontSize=9.8,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#334155"),
            spaceAfter=8,
        ),
        "Section": ParagraphStyle(
            "KodaSection",
            parent=base["Heading2"],
            fontName=FONT_BOLD,
            fontSize=12.2,
            leading=16,
            textColor=colors.HexColor("#173A5E"),
            spaceBefore=4,
            spaceAfter=3,
        ),
        "Body": ParagraphStyle(
            "KodaBody",
            parent=base["BodyText"],
            fontName=FONT_BODY,
            fontSize=9.2,
            leading=13.8,
            textColor=colors.HexColor("#1F2937"),
        ),
        "Small": ParagraphStyle(
            "KodaSmall",
            parent=base["BodyText"],
            fontName=FONT_BODY,
            fontSize=8.2,
            leading=11.5,
            textColor=colors.HexColor("#374151"),
        ),
        "TableHeader": ParagraphStyle(
            "KodaTableHeader",
            parent=base["BodyText"],
            fontName=FONT_BOLD,
            fontSize=8.1,
            leading=10.5,
            textColor=colors.white,
        ),
        "TableBody": ParagraphStyle(
            "KodaTableBody",
            parent=base["BodyText"],
            fontName=FONT_BODY,
            fontSize=7.6,
            leading=10.2,
            textColor=colors.HexColor("#1F2937"),
        ),
    }

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=17 * mm,
        rightMargin=17 * mm,
        topMargin=15 * mm,
        bottomMargin=18 * mm,
    )
    story = [
        p(f"K-ODA Compass Case Study: {s['country']} {s['sector']}", styles["Title"]),
        p("데이터 기반 공공투자 우선순위 산출 및 리스크 조정 의사결정 모델", styles["Subtitle"]),
        HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#AAB7C4")),
        Spacer(1, 8),
    ]

    score_rows = [
        ["항목", "값", "의미"],
        ["사용자", s["user_type"], s["persona"]],
        ["종합순위/점수", f"{app.fmt_int(row.get('Rank_V21'))}위 / {fmt(row.get('K_ODA_Opportunity_Score_V21'))}점", app.display_candidate_type(row.get("Candidate_Type_V21"))],
        ["추천분야", app.safe_text(row.get("Recommended_Service_Angle_V2")), s["decision"]],
    ]
    story.extend(heading("1. Service Use Case", styles))
    story.append(make_table(score_rows, [28 * mm, 42 * mm, 92 * mm], styles))

    contrib_rows = [["구성요소", "원점수", "가중기여", "해석"]]
    for _, r in contribution.head(5).iterrows():
        contrib_rows.append([r["구성요소"], fmt(r["원점수"]), fmt(r["기여점수"]), r["해석"]])
    story.extend(heading("2. Risk-adjusted Score Logic", styles))
    story.append(make_table(contrib_rows, [34 * mm, 22 * mm, 24 * mm, 82 * mm], styles))
    story.append(Spacer(1, 5))
    story.append(
        p(
            "개발수요, 한국 협력기반, 분야 적합성, 정책정합성, 실행가능성, 데이터 신뢰도를 결합해 ODA를 공공투자 포트폴리오처럼 비교합니다.",
            styles["Body"],
        )
    )

    workflow_rows = [
        ["단계", "서비스 화면", "산출물"],
        ["1", "국가순위/프로필", "Top 50 후보국, 점수 분해, 국가별 WDI/KOICA 요약"],
        ["2", "AI Builder", "RAG Evidence Pack 고정 후 생성문마다 [E01] citation 삽입"],
        ["3", "AI검증", "RAG 문서 수, CPS 커버리지, 민감도 분석, 점수 재현성 확인"],
        ["4", "배포/QR", "Streamlit URL, GitHub URL, 심사용 QR, PDF export"],
    ]
    story.extend(heading("3. Product Workflow", styles))
    story.append(make_table(workflow_rows, [18 * mm, 42 * mm, 102 * mm], styles))

    evidence_rows = [["ID", "유형", "근거 요약", "출처"]]
    for _, d in docs.head(9).iterrows():
        evidence_rows.append([f"[{d['Citation_ID']}]", d["Source_Type"], d["Title"], d["Citation"]])
    story.extend(heading("4. Evidence Pack", styles))
    story.append(make_table(evidence_rows, [15 * mm, 28 * mm, 55 * mm, 64 * mm], styles))

    story.append(PageBreak())
    story.extend(heading("5. Case Decision", styles))
    story.append(p(s["decision"], styles["Body"]))
    story.extend(heading("6. Pilot and Scale Roadmap", styles))
    roadmap_rows = [
        ["기간", "목표", "검증자료"],
        ["0-1개월", "CPS 원문, KOICA/WDI 근거팩, 국가 프로필 재확인", "Evidence Pack, 이해관계자 맵"],
        ["1-2개월", "현지 파트너 인터뷰와 KPI baseline 확정", "인터뷰 노트, baseline sheet"],
        ["3-6개월", "파일럿 운영과 데이터 품질점검", "운영 로그, KPI dashboard"],
        ["6-12개월", "확장 제안서와 예산/운영주체 확정", "사업제안서, 예산안, MOU"],
    ]
    story.append(make_table(roadmap_rows, [24 * mm, 86 * mm, 52 * mm], styles))
    story.extend(heading("7. Business and Diffusion Model", styles))
    story.append(
        p(
            "초기에는 CSO, 지자체, 기업의 사업기획 시간을 줄이는 decision-support SaaS로 검증하고, 이후 KOICA/지자체/대학/개발컨설팅 기관용 API와 PDF 템플릿 패키지로 확산합니다.",
            styles["Body"],
        )
    )
    story.extend(heading("8. Risk Controls", styles))
    controls = [
        ["근거 환각", "Evidence Pack 밖의 주장 금지, citation ID 자동 삽입"],
        ["정책 proxy 한계", "CPS 원문과 현지 인터뷰로 최종 타당성 재검증"],
        ["OCR 누락", "CPS OCR Coverage Report로 image-only PDF를 별도 추적"],
        ["사업화 리스크", "파일럿 KPI와 운영주체를 1단계에서 확정"],
    ]
    story.append(make_table([["리스크", "통제방안"], *controls], [42 * mm, 120 * mm], styles))
    story.append(Spacer(1, 6))
    story.append(
        p(
            "This case study is generated from the committed K-ODA Compass RAG data files and is intended as a service-style submission artifact.",
            styles["Small"],
        )
    )
    doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)


def main() -> None:
    out_dir = Path("sample_outputs/case_studies")
    out_dir.mkdir(parents=True, exist_ok=True)

    data = app.load_all_data()
    corpus = app.build_rag_corpus(
        data["master"],
        data["wdi"],
        data["projects"],
        data["policy_risk"],
        data["sector_summary"],
        data["cps_pdf"],
    )

    index_lines = ["# Service-style Case Studies", ""]
    for scenario in SCENARIOS:
        row = app.get_country_row(data["master"], scenario["country"])
        docs = app.retrieve_rag_evidence(
            corpus,
            scenario["country"],
            scenario["sector"],
            scenario["keywords"],
            row,
            top_k=16,
        )
        contribution = app.score_contribution_table(row, data["weights"])
        md_text = case_markdown(scenario, row, docs, contribution)
        md_path = out_dir / f"{scenario['slug']}_case_study.md"
        pdf_path = out_dir / f"{scenario['slug']}_case_study.pdf"
        md_path.write_text(md_text, encoding="utf-8")
        build_pdf(pdf_path, scenario, row, docs, contribution)
        index_lines.extend(
            [
                f"## {scenario['country']} - {scenario['sector']}",
                f"- User: {scenario['user_type']}",
                f"- PDF: `{pdf_path.name}`",
                f"- Markdown: `{md_path.name}`",
                "",
            ]
        )

    (out_dir / "README.md").write_text("\n".join(index_lines), encoding="utf-8")
    print(f"Generated {len(SCENARIOS)} service-style case studies in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
