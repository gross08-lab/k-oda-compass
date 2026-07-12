#!/usr/bin/env python3
"""Generate the audited 10-page K-ODA Compass submission proposal.

Pages 1-6 preserve the supplied, already-polished proposal pages. This script
applies two narrow wording corrections to those pages, generates replacement
pages 7-10 from verified repository evidence, adds page numbers, and writes a
single reproducible final PDF.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
SOURCE_DIR = SCRIPT_DIR / "source_pages"
INTERMEDIATE_DIR = SCRIPT_DIR / "intermediate"
FINAL_PDF = SCRIPT_DIR / "KODA_Compass_Proposal_FINAL_SUBMISSION_AI_UPGRADE.pdf"

LIVE_URL = "https://k-oda-compass.streamlit.app"
GITHUB_URL = "https://github.com/gross08-lab/k-oda-compass"
APP_VERSION = "v2.1"
GIT_COMMIT = "ai-evidence-upgrade"
VERIFICATION_DATE = "2026-07-13"

W, H = A4
M = 29

NAVY = colors.HexColor("#173F67")
BLUE = colors.HexColor("#3D73A5")
GREEN = colors.HexColor("#2E7A62")
ORANGE = colors.HexColor("#B86B16")
RED = colors.HexColor("#A64B43")
TEXT = colors.HexColor("#25384B")
MUTED = colors.HexColor("#647485")
BORDER = colors.HexColor("#A8C0D4")
LIGHT_BLUE = colors.HexColor("#EEF5FA")
LIGHT_GREEN = colors.HexColor("#EAF5F0")
LIGHT_ORANGE = colors.HexColor("#FFF3E2")
LIGHT_RED = colors.HexColor("#FBEDEB")
LIGHT_GRAY = colors.HexColor("#F5F7F9")
WHITE = colors.white


def register_fonts() -> None:
    font_dir = REPO_ROOT / "assets" / "fonts"
    regular = font_dir / "NanumGothic-Regular.ttf"
    bold = font_dir / "NanumGothic-Bold.ttf"
    if not regular.exists() or not bold.exists():
        raise FileNotFoundError(f"Required Korean fonts are missing: {font_dir}")
    pdfmetrics.registerFont(TTFont("NanumGothic", str(regular)))
    pdfmetrics.registerFont(TTFont("NanumGothic-Bold", str(bold)))
    pdfmetrics.registerFontFamily(
        "NanumGothic",
        normal="NanumGothic",
        bold="NanumGothic-Bold",
        italic="NanumGothic",
        boldItalic="NanumGothic-Bold",
    )


def para(
    c: canvas.Canvas,
    text: str,
    x: float,
    top: float,
    width: float,
    *,
    size: float = 8.2,
    leading: float | None = None,
    color: colors.Color = TEXT,
    bold: bool = False,
    align: int = TA_LEFT,
    space_after: float = 0,
) -> float:
    style = ParagraphStyle(
        name="inline",
        fontName="NanumGothic-Bold" if bold else "NanumGothic",
        fontSize=size,
        leading=leading or size * 1.35,
        textColor=color,
        alignment=align,
        spaceAfter=space_after,
        wordWrap="CJK",
        splitLongWords=True,
    )
    p = Paragraph(text, style)
    _, height = p.wrap(width, H)
    p.drawOn(c, x, top - height)
    return top - height


def section_title(c: canvas.Canvas, number: str, title: str, top: float) -> float:
    return para(
        c,
        f"{number}. {title}",
        M,
        top,
        W - 2 * M,
        size=10.6,
        leading=13.2,
        color=NAVY,
        bold=True,
    ) - 6


def rect(
    c: canvas.Canvas,
    x: float,
    top: float,
    width: float,
    height: float,
    *,
    fill: colors.Color = WHITE,
    stroke: colors.Color = BORDER,
    line_width: float = 0.55,
) -> None:
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(line_width)
    c.rect(x, top - height, width, height, fill=1, stroke=1)


def card(
    c: canvas.Canvas,
    x: float,
    top: float,
    width: float,
    height: float,
    *,
    title: str,
    body: str,
    fill: colors.Color,
    accent: colors.Color,
    title_size: float = 8.8,
    body_size: float = 7.4,
    align: int = TA_LEFT,
) -> None:
    rect(c, x, top, width, height, fill=fill, stroke=BORDER)
    c.setFillColor(accent)
    c.rect(x, top - 2.2, width, 2.2, fill=1, stroke=0)
    para(
        c,
        title,
        x + 7,
        top - 9,
        width - 14,
        size=title_size,
        leading=title_size * 1.25,
        color=accent,
        bold=True,
        align=align,
    )
    para(
        c,
        body,
        x + 7,
        top - 30,
        width - 14,
        size=body_size,
        leading=body_size * 1.42,
        color=TEXT,
        align=align,
    )


def callout(
    c: canvas.Canvas,
    text: str,
    top: float,
    *,
    height: float = 42,
    fill: colors.Color = LIGHT_BLUE,
    accent: colors.Color = BLUE,
) -> None:
    rect(c, M, top, W - 2 * M, height, fill=fill, stroke=BORDER)
    c.setFillColor(accent)
    c.rect(M, top - height, 2.5, height, fill=1, stroke=0)
    para(c, text, M + 9, top - 8, W - 2 * M - 18, size=7.8, leading=11.1, color=TEXT)


def top_band(c: canvas.Canvas) -> None:
    c.setFillColor(NAVY)
    c.setFont("NanumGothic-Bold", 6.8)
    c.drawString(M + 4, H - 28, "2026 외교 공공데이터·AI 활용 경진대회  |  제품·서비스 개발")
    c.drawRightString(W - M - 4, H - 28, "K-ODA Compass")
    c.setStrokeColor(NAVY)
    c.setLineWidth(0.8)
    c.line(M, H - 34, W - M, H - 34)


def header(c: canvas.Canvas, title: str, subtitle: str) -> None:
    top_band(c)
    para(c, title, M, H - 46, W - 2 * M, size=17.7, leading=21.0, color=NAVY, bold=True)
    para(c, subtitle, M, H - 69, W - 2 * M, size=9.2, leading=11.5, color=MUTED, bold=True)


def footer(c: canvas.Canvas, source: str) -> None:
    para(c, source, M + 2, 31, W - 2 * M - 34, size=5.8, leading=7.2, color=MUTED, align=TA_CENTER)


def table_flowable(
    c: canvas.Canvas,
    data: Sequence[Sequence[str]],
    x: float,
    top: float,
    col_widths: Sequence[float],
    *,
    header_fill: colors.Color = NAVY,
    font_size: float = 6.9,
    leading: float = 9.1,
    row_fills: Sequence[colors.Color] | None = None,
    alignments: Sequence[str] | None = None,
    cell_padding: float = 4.2,
) -> float:
    paragraphs: list[list[Paragraph]] = []
    for row_index, row in enumerate(data):
        p_row: list[Paragraph] = []
        for col_index, value in enumerate(row):
            is_header = row_index == 0
            align = TA_CENTER if is_header else (TA_LEFT if not alignments else {"LEFT": TA_LEFT, "CENTER": TA_CENTER}.get(alignments[col_index], TA_LEFT))
            style = ParagraphStyle(
                name=f"table-{row_index}-{col_index}",
                fontName="NanumGothic-Bold" if is_header else "NanumGothic",
                fontSize=font_size,
                leading=leading,
                textColor=WHITE if is_header else TEXT,
                alignment=align,
                wordWrap="CJK",
            )
            p_row.append(Paragraph(str(value), style))
        paragraphs.append(p_row)

    table = Table(paragraphs, colWidths=list(col_widths), repeatRows=1)
    style_commands: list[tuple] = [
        ("BACKGROUND", (0, 0), (-1, 0), header_fill),
        ("GRID", (0, 0), (-1, -1), 0.45, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), cell_padding),
        ("RIGHTPADDING", (0, 0), (-1, -1), cell_padding),
        ("TOPPADDING", (0, 0), (-1, -1), cell_padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), cell_padding),
    ]
    if row_fills:
        for row_index in range(1, len(data)):
            fill = row_fills[(row_index - 1) % len(row_fills)]
            style_commands.append(("BACKGROUND", (0, row_index), (-1, row_index), fill))
    table.setStyle(TableStyle(style_commands))
    _, height = table.wrap(sum(col_widths), H)
    table.drawOn(c, x, top - height)
    return top - height


def draw_qr(c: canvas.Canvas, url: str, x: float, y: float, size: float) -> None:
    qr = QrCodeWidget(url)
    x1, y1, x2, y2 = qr.getBounds()
    width = x2 - x1
    height = y2 - y1
    drawing = Drawing(size, size, transform=[size / width, 0, 0, size / height, 0, 0])
    drawing.add(qr)
    renderPDF.draw(drawing, c, x, y)


def page_7(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    header(
        c,
        "문장력보다 근거 운영체계: 범용 생성형 AI와의 구조적 비교",
        "모델 성능 경연이 아니라 공공데이터 기반 의사결정 산출물의 구조를 비교한다",
    )
    callout(
        c,
        "<b>비교 해석</b>  현재 보존된 실행 증거는 특정 생성모델 간 통제실험이 아니다. 따라서 모델명이나 API 제공 여부를 단정하지 않고, 동일 입력의 범용 생성형 AI 단독 조건과 K-ODA Compass의 <b>점수·근거·검증 구조</b>를 비교한다.",
        745,
        height=45,
        fill=LIGHT_ORANGE,
        accent=ORANGE,
    )

    y = section_title(c, "1", "공정한 비교 조건", 686)
    gap = 12
    col = (W - 2 * M - gap) / 2
    card(
        c,
        M,
        y,
        col,
        88,
        title="조건 A  |  범용 생성형 AI 단독",
        body="동일 사용자 입력·동일 평가항목<br/>공공데이터 Evidence ID와 PDF 페이지 미제공<br/>표현력과 일반 지식에 의존한 초안",
        fill=LIGHT_BLUE,
        accent=BLUE,
        align=TA_CENTER,
    )
    card(
        c,
        M + col + gap,
        y,
        col,
        88,
        title="조건 B  |  K-ODA Compass",
        body="동일 사용자 입력·동일 평가항목<br/>Score + CPS·KOICA·WDI + Evidence Pack 고정<br/>생성모델과 근거·검증 계층 분리",
        fill=LIGHT_GREEN,
        accent=GREEN,
        align=TA_CENTER,
    )

    y = section_title(c, "2", "구조적 차이", y - 101)
    data = [
        ["평가 축", "범용 생성형 AI 단독", "K-ODA Compass"],
        ["국가·분야 선택", "사용자가 후보를 사전에 지정", "50개국 MCDA 점수와 분야 근거로 우선검토"],
        ["공공데이터 역할", "배경정보 또는 프롬프트 문맥", "KOICA·CPS를 추천·근거검색·Citation의 핵심 자산으로 사용"],
        ["근거 추적", "출처 형식이 출력마다 달라질 수 있음", "Evidence ID·문서명·PDF 페이지·근거등급을 보존"],
        ["설계 가정", "사실과 설계 수치의 경계가 불명확할 수 있음", "A01~A07을 AI 생성 예비 설계 가정으로 분리"],
        ["재현·감사", "대화와 모델 상태에 의존", "점수 기여도·Evidence Pack·품질검사 결과를 함께 저장"],
        ["모델 교체", "모델 변경이 산출물 구조까지 바꿀 수 있음", "근거 객체와 생성엔진을 분리해 모델 중립적으로 운영"],
    ]
    y = table_flowable(
        c,
        data,
        M + 10,
        y,
        [105, 195, 218],
        font_size=6.7,
        leading=8.7,
        row_fills=[WHITE, LIGHT_BLUE],
        alignments=["CENTER", "LEFT", "LEFT"],
        cell_padding=3.5,
    )

    y = section_title(c, "3", "현재 확인된 실행 증거와 해석 경계", y - 12)
    gap = 8
    col = (W - 2 * M - 2 * gap) / 3
    card(
        c,
        M,
        y,
        col,
        100,
        title="실행 증거",
        body="Local RAG로 Proposal·Brief·Evidence Pack과 두 PDF 경로 생성<br/>50개국 점수 가중합 50/50 재현<br/>pytest 38 PASS",
        fill=LIGHT_BLUE,
        accent=BLUE,
    )
    card(
        c,
        M + col + gap,
        y,
        col,
        100,
        title="Citation 표본검수",
        body="3개 국가·분야 조합 9/9 원문 대조<br/>르완다 화면·Brief 표본 8/8 대조<br/><b>표본 범위이며 전체 정확도로 일반화하지 않음</b>",
        fill=LIGHT_GREEN,
        accent=GREEN,
    )
    card(
        c,
        M + 2 * (col + gap),
        y,
        col,
        100,
        title="비교의 한계",
        body="A/B/C 하네스는 구현했으나 API 키 부재로 실제 호출은 0건<br/>따라서 생성 품질 개선이나 인과효과를 주장하지 않음",
        fill=LIGHT_ORANGE,
        accent=ORANGE,
    )

    y = section_title(c, "4", "모델이 바뀌어도 남는 경쟁력", y - 113)
    gap = 8
    col = (W - 2 * M - 2 * gap) / 3
    card(
        c,
        M,
        y,
        col,
        77,
        title="공공데이터 운영체계",
        body="정합화된 국가·분야 데이터와 문서 커버리지 메타데이터",
        fill=LIGHT_BLUE,
        accent=BLUE,
        align=TA_CENTER,
    )
    card(
        c,
        M + col + gap,
        y,
        col,
        77,
        title="근거계보·품질통제",
        body="Evidence Class·Citation 의미 정합성·REVIEW 규칙",
        fill=LIGHT_GREEN,
        accent=GREEN,
        align=TA_CENTER,
    )
    card(
        c,
        M + 2 * (col + gap),
        y,
        col,
        77,
        title="Human-in-the-loop",
        body="현지조사·전문가 검토·최종 사업선정의 책임을 사용자에게 유지",
        fill=LIGHT_ORANGE,
        accent=ORANGE,
        align=TA_CENTER,
    )

    callout(
        c,
        "<b>결론</b>  K-ODA Compass의 차별점은 더 그럴듯한 문장을 자동 생성하는 데 있지 않다. 외교·ODA 공공데이터를 <b>점수 → 근거검색 → Evidence Pack → 초안 → 검토</b>로 연결해, 생성모델이 달라져도 감사 가능한 의사결정 구조를 유지하는 데 있다.",
        y - 90,
        height=47,
        fill=LIGHT_ORANGE,
        accent=ORANGE,
    )
    footer(c, "검증근거: feature_verification.csv · runtime_test_report.md · citation_spotcheck.csv · 모델 중립 비교")
    c.save()


def page_8(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    header(
        c,
        "구현·런타임·Citation을 분리해 검증했다",
        "정량 점수 재현성 · 기능 실행 · 근거 표본대조 · fallback · 남은 한계",
    )
    callout(
        c,
        "<b>검증 원칙</b>  외부 인증이나 전체 정확도를 주장하지 않는다. 저장소 파일·로컬 실행·브라우저 순회·PDF 원문 대조로 확인한 범위만 PASS로 기록하고, 부분 구현과 미검증 외부 경로는 별도 상태로 공개한다.",
        745,
        height=43,
        fill=LIGHT_BLUE,
        accent=BLUE,
    )

    y = section_title(c, "1", "핵심 검증 결과", 688)
    labels = [
        ("50 / 50", "국가 점수 가중합 재현", BLUE, LIGHT_BLUE),
        ("23 / 25", "주요 기능 런타임 검증", GREEN, LIGHT_GREEN),
        ("38 PASS", "pytest", ORANGE, LIGHT_ORANGE),
        ("60", "검증 질의 형식", BLUE, LIGHT_BLUE),
        ("9/9 · 8/8", "서로 다른 Citation 표본", GREEN, LIGHT_GREEN),
        ("0건", "Secret·API 키 노출", ORANGE, LIGHT_ORANGE),
    ]
    gap = 6
    col = (W - 2 * M - 5 * gap) / 6
    for i, (value, label, accent, fill) in enumerate(labels):
        x = M + i * (col + gap)
        rect(c, x, y, col, 72, fill=fill, stroke=BORDER)
        para(c, value, x + 3, y - 13, col - 6, size=13.0, leading=15, color=accent, bold=True, align=TA_CENTER)
        para(c, label, x + 4, y - 40, col - 8, size=6.3, leading=8.2, color=TEXT, align=TA_CENTER)

    y = section_title(c, "2", "검증 매트릭스", y - 85)
    data = [
        ["검증 대상", "실제 결과", "상태", "해석 범위"],
        ["Opportunity Score", "저장 점수 vs 7개 저장 구성점수×가중치<br/>50/50 일치·최대오차 0.005", "PASS", "원자료→구성점수 상류는 미재현"],
        ["검색 Gold Set", "10개 CPS 원문 페이지·60개 질의 형식<br/>동결 test 39건", "PASS", "내부 검증이며 60개 독립 페이지 검수 아님"],
        ["검색 벤치마크", "Recall@5: lexical 1.00 · embedding 0.52<br/>hybrid 0.80 · filtered 0.96", "PASS", "운영 기본 lexical·평균 1.50ms"],
        ["CPS RAG", "20개국·유효 청크 806개<br/>Top50 직접근거 연결 19/50", "PASS", "27개 확보분 전체가 검색 가능하지 않음"],
        ["Citation 표본 A", "3개 국가·분야 조합 9/9 원문 일치", "PASS", "표본 9건에 한정"],
        ["Citation 표본 B", "르완다 화면·Brief CPS 인용 8/8 일치", "PASS", "대표 사례 표본 8건에 한정"],
        ["A/B/C 통제실험", "10사례×3조건 하네스·평가기 구현<br/>실제 생성 호출 0건", "LIMIT", "API 키 부재·성능 비교값 미산출"],
    ]
    y = table_flowable(
        c,
        data,
        M + 5,
        y,
        [102, 238, 55, 142],
        font_size=6.15,
        leading=8.0,
        row_fills=[WHITE, LIGHT_BLUE],
        alignments=["LEFT", "LEFT", "CENTER", "LEFT"],
        cell_padding=3.4,
    )

    y = section_title(c, "3", "분모·검색 선택·계보 범위", y - 10)
    gap = 8
    col = (W - 2 * M - gap) / 2
    card(
        c,
        M,
        y,
        col,
        96,
        title="CPS 27 / 20 / 19 / 806",
        body="27개국분 확보·점검<br/>20개국 텍스트 추출·검색 가능<br/>Top50 중 직접근거 연결 19개국<br/>유효 RAG 청크 806개",
        fill=LIGHT_BLUE,
        accent=BLUE,
    )
    card(
        c,
        M + col + gap,
        y,
        col,
        96,
        title="검색 기본값과 상류 계보",
        body="동결 test에서 lexical이 Recall@5 1.00으로 최고여서 기본값 유지<br/>7개 구성점수: PARTIAL 6 · UNRESOLVED 1<br/><b>원자료→구성점수 완전 재현 0개국</b>",
        fill=LIGHT_ORANGE,
        accent=ORANGE,
    )

    y = section_title(c, "4", "남은 한계와 통제", y - 109)
    limitations = [
        ("OCR", "이미지 중심 CPS 7개 문서는 검색 제외", "OCR 보강 후 동일 Citation 검사"),
        ("점수 계보", "원천값→7개 구성점수의 상류 생성코드 미보존", "저장 구성점수 가중합만 VERIFIED"),
        ("검색", "negative metadata query 거부율 0%", "국가·분야 필터와 불일치율을 함께 공개"),
        ("사용자 검증", "외부 기관 실증·성과 측정 미완료", "90일 전문가·사용자 파일럿 계획"),
    ]
    gap = 6
    col = (W - 2 * M - 3 * gap) / 4
    for i, (title, limit, control) in enumerate(limitations):
        card(
            c,
            M + i * (col + gap),
            y,
            col,
            92,
            title=title,
            body=f"<b>한계</b> {limit}<br/><b>통제</b> {control}",
            fill=[LIGHT_BLUE, LIGHT_GREEN, LIGHT_ORANGE, LIGHT_RED][i],
            accent=[BLUE, GREEN, ORANGE, RED][i],
            title_size=8.2,
            body_size=6.5,
        )

    callout(
        c,
        "<b>책임 있는 해석</b>  점수와 생성문은 자동 사업선정이나 사실성 보증이 아니다. 근거 부족·OCR 미완료·상류 계보 부재를 화면과 문서에 표시하고, 현지 수요조사·전문가 검토·타당성 조사를 최종 판단 조건으로 둔다.",
        y - 105,
        height=44,
        fill=LIGHT_RED,
        accent=RED,
    )
    footer(c, f"검증일 {VERIFICATION_DATE} · 앱 {APP_VERSION} · Git {GIT_COMMIT} · 근거: retrieval_benchmark_summary.json / score_lineage_matrix.csv")
    top_band(c)
    c.save()


def page_9(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    header(
        c,
        "무료 공공기능에서 기관용 검증 워크스페이스로",
        "초기 사용자 · 반복업무 · 운영비용 · 지속가능성 · 공공가치",
    )
    callout(
        c,
        "<b>현재와 계획의 분리</b>  현재는 공개 Streamlit MVP와 다운로드 산출물을 제공한다. 기관별 저장공간·감사로그·협업·정기 갱신은 90일 실증으로 수요와 운영비를 검증한 뒤 확장할 계획이다.",
        745,
        height=42,
        fill=LIGHT_BLUE,
        accent=BLUE,
    )

    y = section_title(c, "1", "공공데이터에서 사용자 검토까지의 운영 루프", 690)
    steps = [
        ("01", "공식 데이터", "수집·버전관리"),
        ("02", "국가·분야", "우선검토"),
        ("03", "Evidence Pack", "근거 고정"),
        ("04", "초안 생성", "Citation 검사"),
        ("05", "사용자 검토", "현지검증·최종판단"),
    ]
    gap = 7
    col = (W - 2 * M - 4 * gap) / 5
    fills = [LIGHT_BLUE, LIGHT_GREEN, LIGHT_ORANGE, LIGHT_BLUE, LIGHT_GREEN]
    accents = [BLUE, GREEN, ORANGE, BLUE, GREEN]
    for i, (num, title, body) in enumerate(steps):
        card(
            c,
            M + i * (col + gap),
            y,
            col,
            79,
            title=f"{num}  {title}",
            body=body,
            fill=fills[i],
            accent=accents[i],
            title_size=7.8,
            body_size=6.7,
            align=TA_CENTER,
        )

    y = section_title(c, "2", "초기 제공 구조", y - 92)
    gap = 8
    col = (W - 2 * M - 2 * gap) / 3
    card(
        c,
        M,
        y,
        col,
        122,
        title="현재  |  무료 공개 MVP",
        body="50개국 Opportunity Score·순위<br/>국가·분야 탐색<br/>CPS lexical 운영 기본·선택형 의미검색<br/>Local RAG Proposal·Brief·Evidence Pack·PDF",
        fill=LIGHT_BLUE,
        accent=BLUE,
    )
    card(
        c,
        M + col + gap,
        y,
        col,
        122,
        title="실증  |  90일 검증 계획",
        body="교수·연구자·CSO·기업 대상 과제형 파일럿<br/>추천 타당성·Citation 수정률·초안 절감시간 측정<br/>피드백 기반 데이터·검토규칙 개선",
        fill=LIGHT_GREEN,
        accent=GREEN,
    )
    card(
        c,
        M + 2 * (col + gap),
        y,
        col,
        122,
        title="향후  |  기관용 기능",
        body="기관별 워크스페이스·권한<br/>버전·감사로그·검토이력<br/>승인형 API·정기 갱신<br/><b>수요·비용 검증 후 제공</b>",
        fill=LIGHT_ORANGE,
        accent=ORANGE,
    )

    y = section_title(c, "3", "최초 사용자와 반복 업무", y - 135)
    data = [
        ["초기 사용자", "반복 업무", "제공 가치", "초기 진입 방식"],
        ["중소 CSO·NGO", "후보국·분야 탐색, 제안서 초안", "공식 근거 탐색시간 단축, 추가 조사사항 명시", "공개 데모 → 과제형 파일럿"],
        ["ODA 참여 기업·스타트업", "시장·정책정합성 예비검토", "한국 협력경험과 CPS 방향 분리 확인", "협회·지원기관 워크숍"],
        ["지자체·대학·연구자", "국가 비교, 수업·연구용 근거 추적", "점수 기여도와 원문 Citation 재현", "연구·교육 사례 모집"],
        ["향후 기관 사용자", "공동 검토, 버전·감사 관리", "조직 단위 재현성과 책임 분담", "검증된 파일럿 후 기관형 제안"],
    ]
    y = table_flowable(
        c,
        data,
        M + 7,
        y,
        [95, 140, 183, 119],
        font_size=6.45,
        leading=8.5,
        row_fills=[WHITE, LIGHT_BLUE],
        alignments=["LEFT", "LEFT", "LEFT", "LEFT"],
        cell_padding=3.7,
    )

    y = section_title(c, "4", "운영비용과 지속가능성", y - 11)
    ops = [
        ("데이터 갱신", "공식 파일·API 수집, 스키마·버전 관리", BLUE, LIGHT_BLUE),
        ("문서 처리", "CPS OCR·청크·페이지 검수", GREEN, LIGHT_GREEN),
        ("AI·인프라", "임베딩 index·모델 cache·회귀 benchmark·선택적 LLM 비용", ORANGE, LIGHT_ORANGE),
        ("품질·지원", "Citation 표본검수·전문가 REVIEW·사용자 지원", RED, LIGHT_RED),
    ]
    gap = 6
    col = (W - 2 * M - 3 * gap) / 4
    for i, (title, body, accent, fill) in enumerate(ops):
        card(
            c,
            M + i * (col + gap),
            y,
            col,
            78,
            title=title,
            body=body,
            fill=fill,
            accent=accent,
            title_size=8.0,
            body_size=6.5,
            align=TA_CENTER,
        )

    y = section_title(c, "5", "공공가치와 책임 있는 확산", y - 91)
    gap = 8
    col = (W - 2 * M - gap) / 2
    card(
        c,
        M,
        y,
        col,
        82,
        title="Social  |  참여기회와 역량",
        body="전문 컨설팅 접근이 어려운 중소 조직에 공개 탐색도구 제공<br/>ODA 데이터·AI 검증·현지조사 역량을 결합한 업무와 교육 수요 창출",
        fill=LIGHT_GREEN,
        accent=GREEN,
    )
    card(
        c,
        M + col + gap,
        y,
        col,
        82,
        title="Governance  |  근거와 책임",
        body="CPS 문서명·페이지, Evidence Class, 설계 가정, REVIEW 상태 공개<br/>자동 선정을 금지하고 사람의 검토·현지검증·최종 책임 유지",
        fill=LIGHT_BLUE,
        accent=BLUE,
    )

    callout(
        c,
        "<b>지속가능성 원칙</b>  무료 공공기능은 데이터 접근성과 투명성을 유지한다. 기관용 기능은 저장·협업·감사·정기 갱신처럼 반복 운영비가 발생하는 기능으로 한정하고, 실증에서 사용자 가치와 지불 의사를 확인한 뒤 단계적으로 설계한다.",
        y - 94,
        height=47,
        fill=LIGHT_ORANGE,
        accent=ORANGE,
    )
    footer(c, "현재: 공개 MVP · 계획: 과제형 파일럿 → 기관용 검증 워크스페이스 · 계약·매출·기관 협의 완료를 주장하지 않음")
    c.save()


def page_10(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    header(
        c,
        "90일 검증으로 국가전략형 ODA 의사결정 인프라로 확장",
        "UPGRADE · VALIDATE · EXPAND  |  공개 저장소와 재현 가능한 실행계획",
    )
    callout(
        c,
        "<b>실행 목표</b>  현재 검증된 MVP를 기준선으로 삼아 OCR·검색·감사기능을 보강하고, 교수·연구자·ODA 실무자 파일럿에서 추천 타당성·Citation 수정률·초안 절감시간을 측정한 뒤 외교 공공데이터 확장 여부를 판단한다.",
        745,
        height=43,
        fill=LIGHT_BLUE,
        accent=BLUE,
    )

    y = section_title(c, "1", "세 단계 실행축", 688)
    gap = 8
    col = (W - 2 * M - 2 * gap) / 3
    card(
        c,
        M,
        y,
        col,
        105,
        title="UPGRADE  |  모델·데이터",
        body="이미지 중심 CPS 7개 문서 OCR<br/>Gold Set·검색 benchmark 회귀 운영<br/>품질검사·문서 메타데이터 보강",
        fill=LIGHT_BLUE,
        accent=BLUE,
        align=TA_CENTER,
    )
    card(
        c,
        M + col + gap,
        y,
        col,
        105,
        title="VALIDATE  |  전문가·사용자",
        body="정책정합성·근거신뢰성·추천타당성 평가<br/>비전문 사용자 과업 성공률 측정<br/>피드백을 점수·프롬프트·검토규칙에 반영",
        fill=LIGHT_GREEN,
        accent=GREEN,
        align=TA_CENTER,
    )
    card(
        c,
        M + 2 * (col + gap),
        y,
        col,
        105,
        title="EXPAND  |  외교 데이터",
        body="재외공관·국가정보 활용 가능성 검토<br/>정책·제도·현지수요·파트너 근거 확장<br/>승인형 API는 이용조건 확인 후 연계",
        fill=LIGHT_ORANGE,
        accent=ORANGE,
        align=TA_CENTER,
    )

    y = section_title(c, "2", "수상 후 90일 실행계획", y - 118)
    data = [
        ["1–30일  |  기준선 고정", "31–60일  |  전문가 파일럿", "61–90일  |  사용자 실증"],
        [
            "현재 점수·검색 benchmark·출력 회귀테스트<br/>CPS OCR·문서 메타데이터 보강<br/>Citation 검사·감사로그 설계",
            "교수·연구자·ODA 실무자 과제평가<br/>정책정합성·근거신뢰성·추천타당성 검토<br/>오류유형과 수정이력 기록",
            "CSO·기업·지자체 후보 사용자 테스트<br/>과업 성공률·소요시간·수정률 측정<br/>기관용 기능의 수요·운영비 검증",
        ],
    ]
    y = table_flowable(
        c,
        data,
        M + 7,
        y,
        [179, 179, 179],
        font_size=6.8,
        leading=9.2,
        row_fills=[LIGHT_BLUE],
        alignments=["LEFT", "LEFT", "LEFT"],
        cell_padding=5.2,
    )

    y = section_title(c, "3", "파일럿 검증 질문과 KPI", y - 12)
    data = [
        ["검증 대상", "검증 질문", "측정 KPI", "판정 용도"],
        ["교수·연구자", "정책논리와 근거 사용이 타당한가", "Citation 수정률·근거등급 적절성", "정책·학술 검증"],
        ["CSO·기업·지자체", "후보 탐색과 초안 작성에 도움이 되는가", "과업 성공률·소요시간·추가 조사 식별", "사용성·현장 적용"],
        ["시스템 운영", "데이터·모델 변경에도 재현되는가", "점수 회귀·문서 버전·오류 복구", "운영 안정성"],
    ]
    y = table_flowable(
        c,
        data,
        M + 7,
        y,
        [95, 200, 150, 92],
        font_size=6.5,
        leading=8.5,
        row_fills=[WHITE, LIGHT_GREEN],
        alignments=["LEFT", "LEFT", "LEFT", "CENTER"],
        cell_padding=3.8,
    )

    y = section_title(c, "4", "외교 공공데이터 확장의 역할", y - 11)
    gap = 6
    col = (W - 2 * M - 3 * gap) / 4
    data_cards = [
        ("정치·제도환경", "정책 지속성과 제도 리스크 보완", BLUE, LIGHT_BLUE),
        ("양국관계", "협력 의제·정책수신 가능성 검토", GREEN, LIGHT_GREEN),
        ("현지 정책동향", "최근 법령·부처전략·국가계획 연결", ORANGE, LIGHT_ORANGE),
        ("실행 가능성", "현지 파트너·지역위험·추가 현장조사", RED, LIGHT_RED),
    ]
    for i, (title, body, accent, fill) in enumerate(data_cards):
        card(
            c,
            M + i * (col + gap),
            y,
            col,
            75,
            title=title,
            body=body,
            fill=fill,
            accent=accent,
            title_size=7.7,
            body_size=6.3,
            align=TA_CENTER,
        )

    y = section_title(c, "5", "공개 저장소와 재현 범위", y - 88)
    rect(c, M + 10, y, W - 2 * M - 20, 92, fill=LIGHT_BLUE, stroke=BORDER)
    c.setFillColor(NAVY)
    c.rect(M + 10, y - 92, 90, 92, fill=1, stroke=0)
    para(c, "OPEN<br/>REPOSITORY", M + 16, y - 29, 78, size=9.2, leading=12.0, color=WHITE, bold=True, align=TA_CENTER)
    para(
        c,
        "<b>GitHub</b>  github.com/gross08-lab/k-oda-compass<br/>앱 코드·가공 CSV·CPS 추출 청크·검증 스크립트를 공개한다.<br/><b>배포 범위</b>  CPS 원본 PDF는 저장소에 포함하지 않고, 추출 청크와 문서 커버리지 메타데이터만 제공한다.",
        M + 112,
        y - 17,
        330,
        size=7.0,
        leading=10.1,
        color=TEXT,
    )
    c.linkURL(GITHUB_URL, (M + 112, y - 67, W - M - 90, y - 11), relative=0)
    draw_qr(c, GITHUB_URL, W - M - 83, y - 82, 68)
    para(c, "코드·검증자료 확인", W - M - 91, y - 84, 84, size=5.8, leading=7.0, color=MUTED, align=TA_CENTER)

    callout(
        c,
        "<b>최종 방향</b>  K-ODA Compass는 AI가 사업을 대신 결정하는 서비스가 아니다. 외교·ODA 공공데이터를 추천·근거검색·초안·검토이력으로 연결해, 더 많은 조직이 근거 기반 ODA 사업기회를 투명하게 검토하도록 돕는 의사결정 인프라이다.",
        y - 105,
        height=47,
        fill=LIGHT_ORANGE,
        accent=ORANGE,
    )
    footer(c, f"Live Demo: {LIVE_URL} · GitHub: {GITHUB_URL} · 계획 항목은 실증 전이며 기관 협의 완료를 의미하지 않음")
    c.linkURL(LIVE_URL, (M, 20, 255, 38), relative=0)
    c.linkURL(GITHUB_URL, (255, 20, 445, 38), relative=0)
    top_band(c)
    c.save()


def correction_overlay(page_number: int, path: Path) -> None:
    """Create narrow evidence-backed corrections for preserved pages 4-6."""
    c = canvas.Canvas(str(path), pagesize=A4)
    if page_number == 1:
        c.setFillColor(WHITE)
        c.setStrokeColor(WHITE)
        c.rect(414, 551, 85, 15, fill=1, stroke=0)
        para(c, "pytest 38 passed", 416, 564, 80, size=6.2, leading=7.5, color=MUTED, align=TA_CENTER)
    elif page_number == 4:
        rect(c, 403, 600, 108, 46, fill=LIGHT_GREEN, stroke=BORDER)
        para(c, "국가·분야 필터", 409, 589, 96, size=6.5, leading=8.1, color=GREEN, bold=True, align=TA_CENTER)
        para(c, "lexical 기본 · embedding·hybrid 선택", 409, 573, 96, size=5.4, leading=6.8, color=TEXT, align=TA_CENTER)
        rect(c, 382, 191, 169, 55, fill=LIGHT_ORANGE, stroke=BORDER)
        para(c, "현재 검색 검증", 390, 179, 153, size=7.5, leading=9.0, color=ORANGE, bold=True, align=TA_CENTER)
        para(c, "60개 질의 형식 비교 완료<br/>운영 기본 lexical · 선택형 의미검색", 391, 159, 151, size=5.7, leading=7.3, color=TEXT, align=TA_CENTER)
    elif page_number == 5:
        rect(c, 212, 684, 156, 62, fill=LIGHT_GREEN, stroke=BORDER)
        para(c, "02  분야 우선검토", 220, 672, 140, size=8.0, leading=9.6, color=GREEN, bold=True, align=TA_CENTER)
        para(
            c,
            "기술환경에너지 · 분야 태그 청크 풀 15건",
            220,
            651,
            140,
            size=6.4,
            leading=8.3,
            color=TEXT,
            align=TA_CENTER,
        )
        # Clarify that 15 is the tagged CPS chunk pool, not the final Evidence Pack count.
        c.setFillColor(WHITE)
        c.setStrokeColor(WHITE)
        c.rect(339, 364, 216, 39, fill=1, stroke=0)
        para(
            c,
            "KOICA 가공 레코드 78건, <b>CPS 분야 태그 청크 풀 15건</b>, WDI 보조 신호와 위험·추가 검증사항을 검토한 뒤 AI Builder를 연다. 최종 Evidence Pack은 직접근거 4건을 채택한다.",
            342,
            399,
            208,
            size=5.8,
            leading=7.4,
            color=TEXT,
        )
    elif page_number == 6:
        # The runtime-verified Brief PDF is not necessarily one page.
        rect(c, 168, 580, 130, 89, fill=LIGHT_GREEN, stroke=BORDER)
        para(c, "핵심 Brief", 174, 565, 118, size=8.3, leading=10.0, color=GREEN, bold=True, align=TA_CENTER)
        para(
            c,
            "핵심 사업개념·선정근거·추가 검토사항을 요약",
            176,
            541,
            114,
            size=6.0,
            leading=8.0,
            color=TEXT,
            align=TA_CENTER,
        )
    c.save()


def page_number_overlay(page_number: int, path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setFillColor(MUTED)
    c.setFont("NanumGothic", 5.8)
    c.drawRightString(W - M, 14, f"{page_number} / 10")
    c.save()


def rasterized_source_page(page_number: int, path: Path) -> None:
    image_path = SOURCE_DIR / f"{page_number}.png"
    if not image_path.exists():
        raise FileNotFoundError(image_path)
    c = canvas.Canvas(str(path), pagesize=A4)
    c.drawImage(str(image_path), 0, 0, W, H, preserveAspectRatio=False, mask="auto")
    c.save()


def merge_pdf(generated_pages: dict[int, Path]) -> None:
    writer = PdfWriter()
    for page_number in range(1, 11):
        if page_number <= 6:
            source = SOURCE_DIR / f"{page_number}.pdf"
        else:
            source = generated_pages[page_number]
        if page_number in {5, 6}:
            source = INTERMEDIATE_DIR / f"rasterized_source_{page_number}.pdf"
            rasterized_source_page(page_number, source)
        if not source.exists():
            raise FileNotFoundError(source)
        page = PdfReader(str(source)).pages[0]

        if page_number in {1, 4, 5, 6}:
            correction_path = INTERMEDIATE_DIR / f"correction_{page_number}.pdf"
            correction_overlay(page_number, correction_path)
            page.merge_page(PdfReader(str(correction_path)).pages[0])

        number_path = INTERMEDIATE_DIR / f"page_number_{page_number}.pdf"
        page_number_overlay(page_number, number_path)
        page.merge_page(PdfReader(str(number_path)).pages[0])
        writer.add_page(page)

    writer.add_metadata(
        {
            "/Title": "K-ODA Compass 2026 외교 공공데이터·AI 활용 경진대회 최종 제안서",
            "/Author": "K-ODA Compass",
            "/Subject": "제품·서비스 개발 부문 최종 제출본",
            "/Keywords": "KOICA, CPS, ODA, public data, RAG, Evidence Pack",
            "/Creator": "K-ODA Compass audited proposal generator",
        }
    )
    with FINAL_PDF.open("wb") as handle:
        writer.write(handle)


def main() -> None:
    register_fonts()
    INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
    generated_pages = {
        7: INTERMEDIATE_DIR / "page_07.pdf",
        8: INTERMEDIATE_DIR / "page_08.pdf",
        9: INTERMEDIATE_DIR / "page_09.pdf",
        10: INTERMEDIATE_DIR / "page_10.pdf",
    }
    page_7(generated_pages[7])
    page_8(generated_pages[8])
    page_9(generated_pages[9])
    page_10(generated_pages[10])
    merge_pdf(generated_pages)
    print(FINAL_PDF)


if __name__ == "__main__":
    main()
