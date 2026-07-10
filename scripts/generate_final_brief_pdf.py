from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "FINAL_SUBMISSION_BRIEF.pdf"


def register_font() -> str:
    candidates = [
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    ]
    for path in candidates:
        if Path(path).exists():
            pdfmetrics.registerFont(TTFont("KoreanBase", path))
            return "KoreanBase"
    return "Helvetica"


def p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text.replace("\n", "<br/>"), style)


def main() -> None:
    font = register_font()
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=13 * mm,
        bottomMargin=12 * mm,
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "TitleKR",
        parent=styles["Title"],
        fontName=font,
        fontSize=19,
        leading=23,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#111111"),
        spaceAfter=5,
    )
    h = ParagraphStyle(
        "HeadingKR",
        parent=styles["Heading2"],
        fontName=font,
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor("#111111"),
        spaceBefore=5,
        spaceAfter=3,
    )
    body = ParagraphStyle(
        "BodyKR",
        parent=styles["BodyText"],
        fontName=font,
        fontSize=8.7,
        leading=11.2,
        textColor=colors.HexColor("#222222"),
        spaceAfter=3,
    )
    small = ParagraphStyle(
        "SmallKR",
        parent=styles["BodyText"],
        fontName=font,
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#333333"),
    )
    story = []
    story.append(p("K-ODA Compass RAG 최종 제출 브리프", title))
    story.append(
        p(
            "외교·개발협력 공공데이터를 국가 선정, 분야 추천, CPS 정책정합성 검토, 근거 기반 사업기획서 생성까지 연결하는 Evidence-grounded AI ODA 기획 지원 서비스입니다.",
            body,
        )
    )

    metrics = [
        ["분석 대상", "50개국"],
        ["KOICA 사업근거", "12,436건"],
        ["WDI 최신지표", "500행 / 10개 지표"],
        ["CPS PDF 근거", "20개국 / 806개 chunk"],
        ["CPS OCR 감사", "27개 PDF / 663p 텍스트 / 7개 OCR 대상"],
        ["분야 포트폴리오", "669개 국가·분야 조합"],
    ]
    table = Table(metrics, colWidths=[45 * mm, 118 * mm])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font),
                ("FONTSIZE", (0, 0), (-1, -1), 8.6),
                ("LEADING", (0, 0), (-1, -1), 10),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EFEFEF")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#111111")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B8BCC4")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 4))

    story.append(p("심사 관점별 답", h))
    criteria = [
        ["공공데이터", "KOICA, WDI, CPS PDF, OCR 커버리지 감사, 정책·리스크 proxy를 하나의 판단 흐름으로 결합"],
        ["AI 혁신성", "CPS/KOICA/WDI 근거를 먼저 검색하고 생성문마다 [E01] citation을 삽입"],
        ["서비스 완성도", "Streamlit 앱, AI Builder, AI검증, 심사모드, PDF/brief/evidence export 구현"],
        ["검증 가능성", "점수 재현성, RAG 코퍼스 통계, CPS 텍스트/OCR 커버리지, 민감도 분석, Model/Data Card 제공"],
        ["실사용성", "CSO, 지자체, 기업, 정책담당자가 국가·분야·근거·위험요인·KPI를 바로 확보"],
    ]
    crit_table = Table(criteria, colWidths=[31 * mm, 132 * mm])
    crit_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font),
                ("FONTSIZE", (0, 0), (-1, -1), 7.6),
                ("LEADING", (0, 0), (-1, -1), 9.2),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F2F2F2")),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#C8CCD2")),
                ("TOPPADDING", (0, 0), (-1, -1), 3.4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.4),
            ]
        )
    )
    story.append(crit_table)

    story.append(p("대표 시연", h))
    story.append(
        p(
            "AI Builder에서 ‘CSO 탄자니아 공공행정’을 선택하고 RAG형 사업기획서를 생성합니다. 이후 citation 표에서 CPS PDF, KOICA, WDI, 정책·리스크 근거를 확인하고 AI검증 탭에서 점수 재현성·CPS 커버리지·OCR 대상 페이지·민감도 분석을 보여줍니다.",
            body,
        )
    )
    story.append(p("압도적 차별점", h))
    story.append(
        p(
            "이 제출물은 대시보드에서 멈추지 않고, 국가 추천 이유와 정책 문서 근거, 과거 KOICA 사업 맥락, 개발수요 지표, 리스크 보완 논리를 실제 제출 가능한 사업기획 초안으로 변환합니다. LLM 모드는 Evidence Pack 안의 근거만 쓰도록 제한하고, API 키가 없어도 로컬 RAG fallback으로 데모가 유지됩니다.",
            body,
        )
    )
    story.append(p("남은 배포 액션", h))
    story.append(
        p(
            "GitHub 저장소 URL 생성 후 push, Streamlit Cloud에서 app.py 배포, 배포 URL을 README·앱 배포 탭·발표자료·QR에 반영하면 최종 제출 형태가 완성됩니다.",
            small,
        )
    )
    doc.build(story)
    print(OUT)


if __name__ == "__main__":
    main()
