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
FINAL_PDF = SCRIPT_DIR / "KODA_Compass_Proposal_FINAL_SUBMISSION_1800.pdf"

LIVE_URL = "https://k-oda-compass.streamlit.app"
GITHUB_URL = "https://github.com/gross08-lab/k-oda-compass"
APP_VERSION = "v2.1"
GIT_COMMIT = "12701bd"
VERIFICATION_DATE = "2026-07-14"

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


def page_1(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    top_band(c)
    para(c, "K-ODA Compass", M, H - 55, W - 2 * M, size=27, leading=31, color=NAVY, bold=True)
    para(
        c,
        "국가·분야 우선순위부터 CPS 원문 근거, Evidence Pack, 사업기획서까지 연결하는<br/><b>외교·ODA AI 근거 운영체계</b>",
        M,
        H - 91,
        W - 2 * M - 92,
        size=12.3,
        leading=17.0,
        color=TEXT,
    )
    para(c, "LIVE DEMO", W - M - 81, H - 66, 80, size=6.2, leading=7.4, color=BLUE, bold=True, align=TA_CENTER)
    draw_qr(c, LIVE_URL, W - M - 76, H - 146, 70)
    c.linkURL(LIVE_URL, (W - M - 80, H - 148, W - M, H - 55), relative=0)

    callout(
        c,
        "<b>제품 정체성</b>  단순 ODA 추천이나 생성형 AI 문서작성이 아니다. 외교·ODA 공공데이터를 <b>점수·검색·근거·Citation·설계가정·출력</b>으로 분리하고 각 계층을 검증·감사하는 모델 중립적 운영체계다.",
        690,
        height=48,
    )

    y = section_title(c, "1", "검증된 제품 규모", 625)
    kpis = [
        ("50개국", "Opportunity Score·순위", BLUE, LIGHT_BLUE),
        ("12,436건", "KOICA 가공 레코드", GREEN, LIGHT_GREEN),
        ("27개국", "CPS 확보 · 검색 가능", ORANGE, LIGHT_ORANGE),
        ("1,100개", "유효 CPS RAG 청크", BLUE, LIGHT_BLUE),
        ("9개 화면", "탐색·검증·생성·배포", GREEN, LIGHT_GREEN),
        ("5종 출력", "MD 3종 · PDF 2종", ORANGE, LIGHT_ORANGE),
    ]
    gap = 7
    col = (W - 2 * M - 2 * gap) / 3
    for i, (value, label, accent, fill) in enumerate(kpis):
        row, pos = divmod(i, 3)
        x = M + pos * (col + gap)
        top = y - row * 75
        rect(c, x, top, col, 66, fill=fill, stroke=BORDER)
        para(c, value, x + 5, top - 12, col - 10, size=14.2, leading=16, color=accent, bold=True, align=TA_CENTER)
        para(c, label, x + 5, top - 41, col - 10, size=6.5, leading=8.2, color=TEXT, align=TA_CENTER)

    y = section_title(c, "2", "공공데이터가 작동 제품으로 전환되는 흐름", y - 151)
    flow = ["50개국<br/>점수", "국가·분야<br/>우선검토", "CPS 원문<br/>검색", "Evidence<br/>Pack", "Citation·<br/>가정분리", "5종<br/>문서출력"]
    gap = 8
    col = (W - 2 * M - 5 * gap) / 6
    for i, label in enumerate(flow):
        x = M + i * (col + gap)
        rect(c, x, y, col, 66, fill=[LIGHT_BLUE, LIGHT_GREEN, LIGHT_ORANGE][i % 3], stroke=BORDER)
        para(c, f"0{i + 1}", x + 4, y - 10, col - 8, size=6.5, leading=7.5, color=[BLUE, GREEN, ORANGE][i % 3], bold=True, align=TA_CENTER)
        para(c, label, x + 4, y - 29, col - 8, size=7.0, leading=9.0, color=TEXT, bold=True, align=TA_CENTER)
        if i < len(flow) - 1:
            para(c, "→", x + col, y - 30, gap, size=8, leading=9, color=BLUE, bold=True, align=TA_CENTER)

    y = section_title(c, "3", "실제 접근 경로", y - 81)
    gap = 10
    col = (W - 2 * M - gap) / 2
    card(c, M, y, col, 86, title="LIVE DEMO", body="Streamlit 기반 실제 작동 서비스<br/>9개 화면 · Local RAG · 5종 출력", fill=LIGHT_BLUE, accent=BLUE, align=TA_CENTER)
    card(c, M + col + gap, y, col, 86, title="OPEN REPOSITORY", body="앱 코드·가공 데이터·검증 스크립트<br/>검색 benchmark·계보 감사 결과 공개", fill=LIGHT_GREEN, accent=GREEN, align=TA_CENTER)
    c.linkURL(LIVE_URL, (M, y - 86, M + col, y), relative=0)
    c.linkURL(GITHUB_URL, (M + col + gap, y - 86, W - M, y), relative=0)
    callout(c, "<b>핵심 가치</b>  공공데이터의 추천 근거와 생성문서의 출처를 같은 Evidence ID 체계로 연결해, 사용자가 판단 이유와 남은 가정을 함께 검토할 수 있다.", y - 100, height=44, fill=LIGHT_ORANGE, accent=ORANGE)
    footer(c, f"Live Demo: {LIVE_URL}  ·  GitHub: {GITHUB_URL}")
    c.save()


def page_2(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    header(c, "분절된 공공데이터를 검토 가능한 ODA 사업근거로", "문제 구조 · 핵심 사용자 · 반복과업 · 해결 흐름")
    callout(c, "<b>문제정의</b>  데이터 부족보다 더 큰 문제는 서로 다른 기관·파일·문서의 근거가 국가선정, 분야검토, 정책정합성, 생성문서까지 연결되지 않는다는 점이다.", 745, height=43)

    y = section_title(c, "1", "세 가지 구조적 실패", 687)
    gap = 8
    col = (W - 2 * M - 2 * gap) / 3
    failures = [
        ("01  데이터 분절", "기관·파일·지표별로 분리되어 국가·분야 단위 재사용이 어렵다.", BLUE, LIGHT_BLUE),
        ("02  원문 추적 단절", "추천 결과가 어떤 CPS 문장과 PDF 페이지에 근거했는지 확인하기 어렵다.", GREEN, LIGHT_GREEN),
        ("03  사실·가정 혼합", "생성형 AI 결과에서 공공데이터 사실, 정책근거, 설계가정이 섞인다.", ORANGE, LIGHT_ORANGE),
    ]
    for i, (title, body, accent, fill) in enumerate(failures):
        card(c, M + i * (col + gap), y, col, 104, title=title, body=body, fill=fill, accent=accent, title_size=9.0, body_size=7.0)

    y = section_title(c, "2", "해결 흐름", y - 118)
    flow = ["공공데이터<br/>점수", "CPS 원문<br/>검색", "Evidence<br/>Pack", "Citation", "가정 분리", "제출 가능한<br/>기획문서"]
    gap = 7
    col = (W - 2 * M - 5 * gap) / 6
    for i, label in enumerate(flow):
        x = M + i * (col + gap)
        rect(c, x, y, col, 60, fill=[LIGHT_BLUE, LIGHT_GREEN, LIGHT_ORANGE][i % 3], stroke=BORDER)
        para(c, label, x + 4, y - 20, col - 8, size=7.1, leading=9.2, color=TEXT, bold=True, align=TA_CENTER)
        if i < 5:
            para(c, "→", x + col, y - 27, gap, size=8, leading=9, color=BLUE, bold=True, align=TA_CENTER)

    y = section_title(c, "3", "핵심 사용자", y - 74)
    users = ["CSO·NGO", "기업", "지방자치단체", "연구자", "ODA 신규 담당자"]
    gap = 7
    col = (W - 2 * M - 4 * gap) / 5
    for i, label in enumerate(users):
        card(c, M + i * (col + gap), y, col, 69, title=label, body=["공모·제안", "시장·정책", "국제협력", "분석·교육", "업무 진입"][i], fill=[LIGHT_BLUE, LIGHT_GREEN, LIGHT_ORANGE, LIGHT_BLUE, LIGHT_GREEN][i], accent=[BLUE, GREEN, ORANGE, BLUE, GREEN][i], title_size=7.8, body_size=6.4, align=TA_CENTER)

    y = section_title(c, "4", "반복과업을 하나의 근거 흐름으로 연결", y - 83)
    tasks = [
        ["반복과업", "현재 부담", "K-ODA Compass 지원"],
        ["후보국 탐색", "여러 파일을 직접 비교", "50개국 점수·순위·기여도"],
        ["분야 우선검토", "과거사업과 현재수요 혼동", "협력기반·CPS·WDI·위험 분리"],
        ["CPS 정책근거 확인", "PDF 원문과 페이지 수작업 검색", "국가·분야 검색·Page·Chunk ID"],
        ["사업 콘셉트 작성", "근거를 다시 정리하고 문서 작성", "Evidence Pack First·5종 출력"],
        ["검토·심사 대응", "사실·가정·추가조사 재분류", "Citation·Evidence Class·A01~A07"],
    ]
    y = table_flowable(c, tasks, M + 15, y, [120, 180, 207], font_size=6.6, leading=8.6, row_fills=[WHITE, LIGHT_BLUE], alignments=["LEFT", "LEFT", "LEFT"], cell_padding=4.1)
    callout(c, "<b>서비스 목표</b>  사용자가 더 많은 문서를 자동 생성하게 하는 것이 아니라, 반복되는 국가·분야·정책근거 검토를 재현 가능하고 감사 가능한 업무로 전환한다.", y - 18, height=45, fill=LIGHT_ORANGE, accent=ORANGE)
    footer(c, "문제 → 사용자 → 반복과업 → 공공데이터 점수·원문검색·근거고정·검토가능 출력")
    c.save()


def page_3(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    header(c, "공공데이터가 없으면 핵심 기능 자체가 작동하지 않는다", "데이터별 직접 기능 · 검증된 규모 · 데이터 부재 시 소실 기능")
    callout(c, "<b>직접 활용 구조</b>  구조화 데이터 3개 그룹과 비정형 CPS 문서 1개 그룹을 국가·분야 기준으로 연결하고, 추천·검색·근거·Citation·출력에 직접 투입한다.", 745, height=43)

    y = section_title(c, "1", "네 데이터 그룹과 직접 기능", 688)
    gap = 7
    col = (W - 2 * M - 3 * gap) / 4
    sources = [
        ("KOICA ODA", "가공 사업 레코드", "12,436건", "한국 협력기반<br/>분야 경험·사업분포", BLUE, LIGHT_BLUE),
        ("통합개발지표", "KOICA 비교지표", "2023.6.14", "개발수요·취약성<br/>위험·실행가능성", GREEN, LIGHT_GREEN),
        ("World Bank WDI", "국제 보완지표", "10개 코드 · 481건", "국제비교·최신값<br/>데이터 신뢰도 보완", ORANGE, LIGHT_ORANGE),
        ("국가별 CPS", "비정형 정책문서", "27개국분", "정책정합·중점분야<br/>원문 Citation", BLUE, LIGHT_BLUE),
    ]
    for i, (title, subtitle, value, body, accent, fill) in enumerate(sources):
        x = M + i * (col + gap)
        rect(c, x, y, col, 144, fill=fill, stroke=BORDER)
        para(c, title, x + 6, y - 12, col - 12, size=8.6, leading=10.2, color=accent, bold=True, align=TA_CENTER)
        para(c, subtitle, x + 6, y - 34, col - 12, size=6.0, leading=7.2, color=MUTED, align=TA_CENTER)
        para(c, value, x + 5, y - 58, col - 10, size=12.0, leading=14, color=accent, bold=True, align=TA_CENTER)
        para(c, body, x + 8, y - 92, col - 16, size=6.7, leading=8.7, color=TEXT, align=TA_CENTER)

    y = section_title(c, "2", "데이터가 서비스 결과로 전환되는 구조", y - 158)
    data = [
        ["데이터", "판단·검색 역할", "직접 연결되는 서비스 기능"],
        ["KOICA 가공 레코드", "한국 협력기반·분야별 기존 경험", "국가·분야 우선검토·유사 협력사례"],
        ["KOICA 통합개발지표", "개발수요·취약성·실행환경 비교", "7개 구성점수·Opportunity Score"],
        ["World Bank WDI", "국제 비교 보조신호·최신 관측값", "국가 프로필·Evidence Pack 보조출처"],
        ["CPS PDF", "정책방향·중점분야 원문", "정책정합성·Page Citation·직접근거"],
    ]
    y = table_flowable(c, data, M + 13, y, [125, 190, 218], font_size=6.6, leading=8.6, row_fills=[WHITE, LIGHT_BLUE], alignments=["LEFT", "LEFT", "LEFT"], cell_padding=4.0)

    y = section_title(c, "3", "CPS 검색·연결 범위", y - 12)
    values = [("27개국", "CPS PDF 확보"), ("27개국", "RAG 검색 가능"), ("26/50", "Top50 CPS 연결"), ("1,100개", "유효 RAG 청크")]
    gap = 7
    col = (W - 2 * M - 3 * gap) / 4
    for i, (value, label) in enumerate(values):
        rect(c, M + i * (col + gap), y, col, 67, fill=[LIGHT_BLUE, LIGHT_GREEN, LIGHT_ORANGE, LIGHT_BLUE][i], stroke=BORDER)
        para(c, value, M + i * (col + gap) + 4, y - 13, col - 8, size=12.5, leading=14, color=[BLUE, GREEN, ORANGE, BLUE][i], bold=True, align=TA_CENTER)
        para(c, label, M + i * (col + gap) + 4, y - 41, col - 8, size=6.4, leading=7.8, color=TEXT, align=TA_CENTER)

    y = section_title(c, "4", "데이터가 없을 때 사라지는 기능", y - 81)
    gap = 8
    col = (W - 2 * M - 2 * gap) / 3
    missing = [
        ("KOICA 없음", "한국 협력기반·분야 경험 판단 불가", BLUE, LIGHT_BLUE),
        ("개발지표 없음", "개발수요·취약성·리스크 비교 약화", GREEN, LIGHT_GREEN),
        ("CPS 없음", "정책정합 원문·페이지 Citation 불가", ORANGE, LIGHT_ORANGE),
    ]
    for i, (title, body, accent, fill) in enumerate(missing):
        card(c, M + i * (col + gap), y, col, 76, title=title, body=body, fill=fill, accent=accent, title_size=8.2, body_size=6.5, align=TA_CENTER)
    callout(c, "<b>결론</b>  공공데이터는 장식적 참고자료가 아니라 추천, 검색, 근거생성, Citation과 문서출력에 직접 연결된다.", y - 89, height=43, fill=LIGHT_ORANGE, accent=ORANGE)
    footer(c, "검증 수치: KOICA 12,436 가공 레코드 · WDI 10개 코드/481건 · CPS 27개국/901 검색페이지/1,100청크")
    c.save()


def page_4(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    header(c, "점수·검색·생성을 분리한 검증 가능한 AI 아키텍처", "MCDA · 데이터·점수 계층 · Evidence RAG · 모델 중립적 생성")
    callout(c, "<b>설계 원칙</b>  검색모델, 점수모델, 생성모델을 분리해 생성모델이 교체돼도 근거 추적성과 감사 가능성을 유지한다.", 745, height=42)

    y = section_title(c, "1", "세 계층 아키텍처", 689)
    gap = 8
    col = (W - 2 * M - 2 * gap) / 3
    card(c, M, y, col, 181, title="A  |  MCDA 점수모델", body="Development Need 25%<br/>Korea Cooperation Base 20%<br/>Sector Fit 15%<br/>Opportunity Gap 10%<br/>Policy Alignment 15%<br/>Risk Feasibility 10%<br/>Data Reliability 5%", fill=LIGHT_BLUE, accent=BLUE, body_size=6.7)
    card(c, M + col + gap, y, col, 181, title="B  |  데이터·점수 계층", body="원자료·외부 데이터<br/>↓<br/>국가명·ISO3·분야코드 정합화<br/>↓<br/>국가·분야 분석 테이블<br/>↓<br/>7개 구성점수<br/>↓<br/>Opportunity Score·순위", fill=LIGHT_GREEN, accent=GREEN, body_size=6.6, align=TA_CENTER)
    card(c, M + 2 * (col + gap), y, col, 181, title="C  |  Evidence RAG", body="CPS PDF<br/>↓ Page·Chunk ID<br/>↓ 국가·분야 필터<br/>↓ 4종 검색모드<br/>↓ Evidence Class<br/>↓ Citation<br/>↓ Evidence Pack", fill=LIGHT_ORANGE, accent=ORANGE, body_size=6.6, align=TA_CENTER)

    y = section_title(c, "2", "네 검색모드와 운영 선택", y - 195)
    data = [
        ["검색모드", "역할", "운영 상태"],
        ["Lexical", "키워드·정책문구 정밀 검색", "앱 기본·fallback"],
        ["Embedding", "의미 기반 후보검색", "lazy loading"],
        ["Hybrid", "lexical·embedding 후보 결합", "선택모드"],
        ["Filtered Hybrid", "국가·분야 필터 후 결합", "동결 benchmark 운영모드"],
    ]
    y = table_flowable(c, data, M + 60, y, [135, 215, 135], font_size=6.8, leading=8.8, row_fills=[WHITE, LIGHT_BLUE], alignments=["LEFT", "LEFT", "CENTER"], cell_padding=3.8)

    y = section_title(c, "3", "운영 안정성과 모델 중립성", y - 12)
    gap = 8
    col = (W - 2 * M - 2 * gap) / 3
    controls = [
        ("Filtered benchmark", "동결 Test Recall@5 1.00·MRR 0.716·평균 11.59ms", BLUE, LIGHT_BLUE),
        ("lazy + fallback", "Embedding은 화면 진입 후 로드하고 실패하면 Lexical로 즉시 전환", GREEN, LIGHT_GREEN),
        ("Local RAG", "외부 LLM 없이도 Evidence Pack과 5종 출력 경로를 유지", ORANGE, LIGHT_ORANGE),
    ]
    for i, (title, body, accent, fill) in enumerate(controls):
        card(c, M + i * (col + gap), y, col, 91, title=title, body=body, fill=fill, accent=accent, title_size=8.2, body_size=6.4)

    y = section_title(c, "4", "검증으로 운영 기본값을 선택", y - 104)
    data = [["Lexical", "Filtered Hybrid", "Hybrid", "Embedding"], ["1.000 · 기본/폴백", "1.000 · benchmark", "0.963 · 비교", "0.268 · 확장"]]
    y = table_flowable(c, data, M + 20, y, [134, 134, 134, 134], font_size=7.0, leading=9.0, row_fills=[LIGHT_BLUE], alignments=["CENTER"] * 4, cell_padding=4.2)
    callout(c, "<b>기술 선택 원칙</b>  복잡한 검색모델을 기술적 유행만으로 채택하지 않고, 독립 Test Set의 Recall과 지연시간을 기준으로 운영 기본값을 선택했다.", y - 18, height=45, fill=LIGHT_ORANGE, accent=ORANGE)
    footer(c, "독립 계층: 7개 구성점수 MCDA · 4종 Retrieval · Evidence Class/Citation · Local 또는 선택적 생성")
    c.save()


def page_7(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    header(
        c,
        "생성모델이 아니라 근거 통제계층의 기여도를 분리해 측정한다",
        "동일모델 A/B/C 실험설계와 현재 구현 범위",
    )
    callout(
        c,
        "<b>현재 상태</b>  10개 사례×3조건 입력·프롬프트·실행 하네스·결정론적 평가기를 구현했다. API 키가 없어 실제 외부 모델 호출은 0건이며, 성능 우위나 효과를 주장하지 않는다.",
        745,
        height=43,
        fill=LIGHT_ORANGE,
        accent=ORANGE,
    )

    y = section_title(c, "1", "동일 생성모델·동일 사례의 세 조건", 689)
    gap = 8
    col = (W - 2 * M - 2 * gap) / 3
    card(
        c, M, y, col, 127,
        title="A  |  GENERIC",
        body="동일 생성모델<br/>사용자 요청만 제공<br/>Score 없음<br/>Evidence Pack 없음<br/>Citation·가정분리 규칙 없음",
        fill=LIGHT_BLUE,
        accent=BLUE,
        align=TA_CENTER,
    )
    card(
        c, M + col + gap, y, col, 127,
        title="B  |  RAW EVIDENCE",
        body="동일 생성모델<br/>사용자 요청 + 검색 원문<br/>구조화 Evidence Pack 통제 없음<br/>Citation·가정분리 강제 없음",
        fill=LIGHT_GREEN,
        accent=GREEN,
        align=TA_CENTER,
    )
    card(
        c, M + 2 * (col + gap), y, col, 127,
        title="C  |  K-ODA CONTROLLED",
        body="동일 생성모델 + 사용자 요청<br/>Opportunity Score·Evidence Pack<br/>Evidence Class·Citation 규칙<br/>A01~A07 가정 분리<br/>근거 부족 시 추가조사 분리",
        fill=LIGHT_ORANGE,
        accent=ORANGE,
        align=TA_CENTER,
    )

    y = section_title(c, "2", "구현된 실험 자산", y - 140)
    card(
        c, M, y, col, 92,
        title="입력·프롬프트",
        body="10개 국가·분야 사례<br/>각 사례에 A/B/C 동일 입력<br/>조건별 프롬프트 고정",
        fill=LIGHT_BLUE,
        accent=BLUE,
        align=TA_CENTER,
    )
    card(
        c, M + col + gap, y, col, 92,
        title="실행 하네스",
        body="동일 생성모델 호출 경로<br/>응답·지연·비용 저장 구조<br/>API 키 부재 시 실행 차단",
        fill=LIGHT_GREEN,
        accent=GREEN,
        align=TA_CENTER,
    )
    card(
        c, M + 2 * (col + gap), y, col, 92,
        title="결정론적 평가기",
        body="Citation validity<br/>미지원 숫자 주장·가정분리<br/>Evidence Class·지연·비용",
        fill=LIGHT_ORANGE,
        accent=ORANGE,
        align=TA_CENTER,
    )

    y = section_title(c, "3", "실행 상태와 다음 측정", y - 105)
    data = [
        ["항목", "현재 상태", "측정 또는 판정"],
        ["입력·프롬프트", "10개 사례×3조건 구현", "버전 고정·재실행 가능"],
        ["하네스·평가기", "구현 완료", "Citation·숫자·가정·Class·지연·비용"],
        ["실제 외부 호출", "0건", "발표심사 전 동일모델로 실행"],
        ["성능·효과", "미산출", "호출 전 우위·개선 효과를 주장하지 않음"],
    ]
    y = table_flowable(
        c, data, M + 18, y, [120, 160, 221],
        font_size=6.8, leading=9.0, row_fills=[WHITE, LIGHT_BLUE],
        alignments=["LEFT", "CENTER", "LEFT"], cell_padding=4.0,
    )

    callout(
        c,
        "현재는 10개 사례×3조건의 재현 가능한 실험 하네스와 결정론적 평가기를 구현한 상태이며, 실제 동일모델 호출과 결과 측정은 발표심사 전 수행한다.",
        y - 15, height=42, fill=LIGHT_RED, accent=RED,
    )
    callout(
        c,
        "<b>결론</b>  K-ODA Compass의 AI 기술은 특정 생성모델의 문장력에 의존하지 않는다. 검색·점수·Evidence Pack·Citation·가정분리 계층을 독립적으로 설계하고, 동일모델 조건에서 각 계층의 기여도를 측정할 수 있는 검증 구조를 구현했다.",
        y - 68,
        height=51,
        fill=LIGHT_ORANGE,
        accent=ORANGE,
    )
    footer(c, "검증근거: controlled_experiment_report.md · controlled_generation_results.jsonl · 외부 모델 호출 0건")
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
        ("120개", "Gold Set 질의", BLUE, LIGHT_BLUE),
        ("4종", "검색모드", GREEN, LIGHT_GREEN),
        ("54 PASS", "pytest", ORANGE, LIGHT_ORANGE),
        ("50 / 50", "점수 가중합 재현", BLUE, LIGHT_BLUE),
        ("47/47", "Citation ID 구조", GREEN, LIGHT_GREEN),
        ("11.59ms", "Filtered 평균", ORANGE, LIGHT_ORANGE),
    ]
    gap = 6
    col = (W - 2 * M - 5 * gap) / 6
    for i, (value, label, accent, fill) in enumerate(labels):
        x = M + i * (col + gap)
        rect(c, x, y, col, 72, fill=fill, stroke=BORDER)
        para(c, value, x + 3, y - 13, col - 6, size=13.0, leading=15, color=accent, bold=True, align=TA_CENTER)
        para(c, label, x + 4, y - 40, col - 8, size=6.3, leading=8.2, color=TEXT, align=TA_CENTER)

    y = section_title(c, "2", "검색 벤치마크와 검증 범위", y - 85)
    data = [
        ["검색방식", "Test Recall@5", "운영 판정"],
        ["Lexical", "1.000", "앱 기본·fallback"],
        ["Filtered Hybrid", "1.000", "동결 benchmark"],
        ["Hybrid", "0.963", "비교모드"],
        ["Embedding", "0.268", "확장모드"],
    ]
    y = table_flowable(
        c, data, M + 70, y, [170, 130, 130],
        font_size=7.1, leading=9.2,
        row_fills=[WHITE, LIGHT_BLUE],
        alignments=["LEFT", "CENTER", "CENTER"], cell_padding=3.5,
    )
    para(
        c,
        "내부 구축 Gold Set 기준이며 외부 전문가 평가 결과가 아니다. 검색결과 확인 전에 원문 PDF 페이지와 정답 청크를 고정하고 dev 29건과 test 91건으로 분리했다.",
        M + 18, y - 7, W - 2 * M - 36, size=6.2, leading=8.2, color=MUTED,
    )

    y = section_title(c, "3", "점수 계보 감사", y - 36)
    gap = 8
    col = (W - 2 * M - gap) / 2
    card(
        c,
        M,
        y,
        col,
        91,
        title="계보 상태",
        body="VERIFIED 1 · PARTIAL 6 · UNRESOLVED 1<br/>저장 구성점수→최종점수 50/50 재현<br/>최대 절대오차 0.005",
        fill=LIGHT_BLUE,
        accent=BLUE,
    )
    card(
        c,
        M + col + gap,
        y,
        col,
        91,
        title="확인 경계",
        body="원자료→7개 구성점수 완전 재현 0개국<br/>확인되지 않은 과거 산식을 기존 점수에 맞춰 역산하지 않고 확인 수준을 분리",
        fill=LIGHT_ORANGE,
        accent=ORANGE,
    )

    y = section_title(c, "4", "근거·출력·fallback 검증", y - 104)
    limitations = [
        ("CPS", "27개국 확보 · 27개국 검색 가능", "Top50 연결 26/50 · 청크 1,100"),
        ("Citation", "ID 구조 47/47 · 원문 표본 17/17", "사람 의미판정 0쌍 · 전체 정확도 아님"),
        ("Local fallback", "API 키 없이 Local RAG 정상", "외부 호출 실패 시 앱 프로세스 유지"),
        ("5종 출력", "Proposal·Brief·Evidence Pack MD", "Proposal PDF · Brief PDF"),
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
            body=f"{limit}<br/>{control}",
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
    footer(c, f"검증일 {VERIFICATION_DATE} · 앱 {APP_VERSION} · Git {GIT_COMMIT} · 내부 Gold Set·점수 계보·Citation 표본 검증")
    top_band(c)
    c.save()


def page_9(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    header(
        c,
        "무료 공공기능에서 기관용 검증 워크스페이스로",
        "현재 공개 MVP · 발표심사 전 기술검증 · 90일 외부 실증 · 향후 기관용",
    )
    callout(
        c,
        "<b>현재와 계획의 분리</b>  공개 MVP만 현재 구현 상태다. 동일모델 A/B/C 실제 호출은 발표심사 전 계획, 외부 사용자 실증은 수상 후 90일 계획, 기관용 기능은 수요·운영비·지불의사 검증 이후 계획이다.",
        745,
        height=42,
        fill=LIGHT_BLUE,
        accent=BLUE,
    )

    y = section_title(c, "1", "검증과 확산의 네 단계", 690)
    steps = [
        ("01", "현재", "무료 공개 MVP"),
        ("02", "발표 전", "기술검증"),
        ("03", "수상 후", "90일 외부 실증"),
        ("04", "향후", "기관용 워크스페이스"),
    ]
    gap = 7
    col = (W - 2 * M - 3 * gap) / 4
    fills = [LIGHT_BLUE, LIGHT_GREEN, LIGHT_ORANGE, LIGHT_RED]
    accents = [BLUE, GREEN, ORANGE, RED]
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

    y = section_title(c, "2", "단계별 범위", y - 92)
    gap = 6
    col = (W - 2 * M - 3 * gap) / 4
    card(
        c,
        M,
        y,
        col,
        122,
        title="현재  |  무료 공개 MVP",
        body="50개국 Score<br/>4종 검색모드·Lexical 기본<br/>Evidence Pack·Local RAG<br/>5종 출력",
        fill=LIGHT_BLUE,
        accent=BLUE,
    )
    card(
        c,
        M + col + gap,
        y,
        col,
        122,
        title="발표 전  |  기술검증",
        body="동일모델 A/B/C 실제 호출<br/>Citation·가정분리·미지원 숫자 실측<br/>Live Demo·스냅샷 회귀검사<br/>결과·프롬프트·평가기 공개",
        fill=LIGHT_GREEN,
        accent=GREEN,
    )
    card(
        c,
        M + 2 * (col + gap),
        y,
        col,
        122,
        title="90일  |  외부 실증",
        body="교수·연구자·ODA 실무자<br/>CSO·기업·지자체<br/>정책정합성·추천타당성<br/>과업 성공률·소요시간 측정",
        fill=LIGHT_ORANGE,
        accent=ORANGE,
    )
    card(
        c,
        M + 3 * (col + gap),
        y,
        col,
        122,
        title="향후  |  기관용",
        body="저장 워크스페이스·권한<br/>감사로그·검토이력·정기 갱신<br/><b>운영비와 지불의사 검증 후 제공</b>",
        fill=LIGHT_RED,
        accent=RED,
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
        "발표심사 전 기술검증 · 90일 외부 실증 · 외교 공공데이터 확장",
    )
    callout(
        c,
        "<b>실행 목표</b>  현재 검증된 MVP를 기준선으로 고정하고, 발표심사 전 동일모델 A/B/C를 실제 측정한다. 수상 후 90일에는 외부 사용자의 정책정합성·추천타당성·과업 성공률을 실증한다.",
        745,
        height=43,
        fill=LIGHT_BLUE,
        accent=BLUE,
    )

    y = section_title(c, "1", "발표심사 전 기술검증", 688)
    gap = 8
    col = (W - 2 * M - 2 * gap) / 3
    card(
        c,
        M,
        y,
        col,
        105,
        title="동일모델 A/B/C",
        body="세 조건 실제 호출<br/>Citation validity 측정<br/>미지원 숫자 주장 측정",
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
        title="근거 통제 측정",
        body="assumption separation<br/>Evidence Class 위반 측정<br/>비용·지연시간 비교",
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
        title="회귀·공개",
        body="Live Demo·제출 스냅샷 회귀검사<br/>결과·프롬프트·평가기<br/>공개 저장소에 기록",
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
        "<b>GitHub</b>  https://github.com/gross08-lab/k-oda-compass<br/>앱 코드·가공 CSV·CPS 추출 청크·검증 스크립트를 공개한다.<br/><b>배포 범위</b>  CPS 원본 PDF는 저장소에 포함하지 않고, 추출 청크와 문서 커버리지 메타데이터만 제공한다.",
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
        "<b>최종 방향</b>  K-ODA Compass는 최신 기술을 많이 붙이는 데 목적이 있지 않다. 검색방식을 독립 Test Set으로 비교하고, 점수·근거·Citation·생성계층을 분리해 검증함으로써 외교·ODA 공공데이터를 재현 가능하고 감사 가능한 의사결정 구조로 전환한다.",
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


def final_page_7(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    header(c, "동일 생성모델에서 근거 통제계층의 기여도를 분리한다", "10개 사례×3조건의 재현 가능한 통제실험 체계")
    callout(c, "<b>실험 목적</b>  생성모델의 차이가 아니라, 동일모델·동일사례에서 Score·Evidence Pack·Citation·가정분리 계층이 출력 통제에 기여하는 방식을 측정한다.", 745, height=43, fill=LIGHT_ORANGE, accent=ORANGE)

    y = section_title(c, "1", "세 가지 통제조건", 688)
    gap = 8
    col = (W - 2 * M - 2 * gap) / 3
    conditions = [
        ("A  |  GENERIC", "동일 생성모델<br/>사용자 요청<br/>별도 근거통제 없음", BLUE, LIGHT_BLUE),
        ("B  |  RAW EVIDENCE", "동일 생성모델<br/>사용자 요청<br/>검색 원문 제공", GREEN, LIGHT_GREEN),
        ("C  |  K-ODA CONTROLLED", "동일 생성모델<br/>Opportunity Score·Evidence Pack<br/>Evidence Class·Citation 규칙<br/>A01~A07 가정 분리<br/>근거 부족 시 추가조사 분리", ORANGE, LIGHT_ORANGE),
    ]
    for i, (title, body, accent, fill) in enumerate(conditions):
        card(c, M + i * (col + gap), y, col, 133, title=title, body=body, fill=fill, accent=accent, title_size=8.7, body_size=6.8, align=TA_CENTER)

    y = section_title(c, "2", "구축된 실험 자산", y - 147)
    assets = [
        ("10개 사례", "국가·분야·사용자 조건", BLUE, LIGHT_BLUE),
        ("3개 조건", "GENERIC·RAW·CONTROLLED", GREEN, LIGHT_GREEN),
        ("고정 프롬프트", "조건별 입력·지시 구조", ORANGE, LIGHT_ORANGE),
        ("실행 하네스", "동일모델 반복 호출 경로", BLUE, LIGHT_BLUE),
        ("결정론적 평가기", "규칙 기반 품질 측정", GREEN, LIGHT_GREEN),
        ("결과 저장구조", "응답·평가·비용·지연", ORANGE, LIGHT_ORANGE),
    ]
    gap = 6
    col = (W - 2 * M - 2 * gap) / 3
    for i, (title, body, accent, fill) in enumerate(assets):
        row, pos = divmod(i, 3)
        card(c, M + pos * (col + gap), y - row * 72, col, 64, title=title, body=body, fill=fill, accent=accent, title_size=7.8, body_size=6.0, align=TA_CENTER)

    y = section_title(c, "3", "결정론적 평가지표", y - 146)
    metrics = ["Citation validity", "unsupported numeric claims", "assumption separation", "Evidence Class compliance", "required section completion", "latency", "token", "cost"]
    gap = 6
    col = (W - 2 * M - 3 * gap) / 4
    for i, metric in enumerate(metrics):
        row, pos = divmod(i, 4)
        rect(c, M + pos * (col + gap), y - row * 55, col, 47, fill=[LIGHT_BLUE, LIGHT_GREEN, LIGHT_ORANGE, LIGHT_RED][pos], stroke=BORDER)
        para(c, metric, M + pos * (col + gap) + 4, y - row * 55 - 16, col - 8, size=6.1, leading=7.5, color=[BLUE, GREEN, ORANGE, RED][pos], bold=True, align=TA_CENTER)

    y = section_title(c, "4", "측정 가능한 통제계층", y - 119)
    data = [
        ["통제계층", "출력에서 확인할 질문", "측정 단위"],
        ["Evidence Pack", "사용한 근거가 고정됐는가", "Citation ID·근거 포함률"],
        ["Citation 규칙", "주장과 출처유형이 일치하는가", "유효·고아·불일치 Citation"],
        ["가정 분리", "설계수치가 사실처럼 혼합되지 않았는가", "A01~A07·미지원 숫자 주장"],
        ["필수 구조", "사업기획 필수 섹션이 완성됐는가", "required section completion"],
    ]
    y = table_flowable(c, data, M + 18, y, [125, 235, 141], font_size=6.4, leading=8.3, row_fills=[WHITE, LIGHT_BLUE], alignments=["LEFT", "LEFT", "LEFT"], cell_padding=3.7)
    callout(c, "<b>결론</b>  K-ODA Compass의 경쟁력은 특정 생성모델의 문장력이 아니라, 생성결과를 근거·가정·검증단위로 통제하는 운영체계에 있다.", y - 18, height=45, fill=LIGHT_ORANGE, accent=ORANGE)
    footer(c, "동일모델 반복 실측은 발표심사 전 검증 스프린트에서 고정한다.")
    c.save()


def final_page_8(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    header(c, "구현·검색·점수·Citation을 독립적으로 검증했다", "동결 Gold Set · Retrieval benchmark · 점수 재현 · Citation 별도 표본")
    callout(c, "<b>검증 원칙</b>  검색결과를 본 뒤 정답을 맞추지 않았다. CPS 원문 PDF 페이지와 정답 청크를 먼저 고정하고 dev/test를 분리한 뒤 네 검색모드를 동일 조건에서 비교했다.", 745, height=43)

    y = section_title(c, "1", "핵심 검증 증거", 688)
    kpis = [
        ("120", "Gold Set", BLUE, LIGHT_BLUE), ("29 / 91", "dev / test", GREEN, LIGHT_GREEN), ("4종", "Retrieval", ORANGE, LIGHT_ORANGE),
        ("54 PASS", "pytest", BLUE, LIGHT_BLUE), ("50 / 50", "Score·순위 재현", GREEN, LIGHT_GREEN), ("0.005", "Max Error", ORANGE, LIGHT_ORANGE),
        ("47 / 47", "Citation ID 구조", BLUE, LIGHT_BLUE), ("17 / 17", "PDF 원문 표본", GREEN, LIGHT_GREEN), ("11.59ms", "Filtered 평균", ORANGE, LIGHT_ORANGE),
    ]
    gap = 6
    col = (W - 2 * M - 2 * gap) / 3
    for i, (value, label, accent, fill) in enumerate(kpis):
        row, pos = divmod(i, 3)
        x = M + pos * (col + gap)
        top = y - row * 60
        rect(c, x, top, col, 52, fill=fill, stroke=BORDER)
        para(c, value, x + 4, top - 9, col - 8, size=11.5, leading=13, color=accent, bold=True, align=TA_CENTER)
        para(c, label, x + 4, top - 33, col - 8, size=5.9, leading=7.2, color=TEXT, align=TA_CENTER)

    y = section_title(c, "2", "검색 성능과 운영 판정", y - 183)
    data = [
        ["검색방식", "Test Recall@5", "운영 판정"],
        ["Lexical", "1.000", "앱 기본·fallback"],
        ["Filtered Hybrid", "1.000", "동결 benchmark 운영모드"],
        ["Hybrid", "0.963", "비교모드"],
        ["Embedding", "0.268", "확장모드"],
    ]
    y = table_flowable(c, data, M + 65, y, [170, 130, 130], font_size=7.0, leading=9.0, row_fills=[WHITE, LIGHT_BLUE], alignments=["LEFT", "CENTER", "CENTER"], cell_padding=3.5)
    para(c, "복잡성이 아니라 실제 평가결과를 기준으로 운영검색 방식을 선택했다.", M + 30, y - 9, W - 2 * M - 60, size=6.6, leading=8.2, color=ORANGE, bold=True, align=TA_CENTER)

    y = section_title(c, "3", "점수 재현과 계보 감사", y - 34)
    gap = 8
    col = (W - 2 * M - gap) / 2
    card(c, M, y, col, 91, title="저장 구성점수 → 최종점수", body="7개 저장 구성점수부터 Opportunity Score와 순위까지<br/><b>50개국 전체 재현 · 최대 절대오차 0.005</b>", fill=LIGHT_BLUE, accent=BLUE, body_size=6.8)
    card(c, M + col + gap, y, col, 91, title="계보 감사 상태", body="VERIFIED 1 · PARTIAL 6 · UNRESOLVED 1<br/>원자료·기준연도·정합화·결측·정규화·산식의 확인 수준을 분리", fill=LIGHT_ORANGE, accent=ORANGE, body_size=6.7)

    y = section_title(c, "4", "Citation 표본과 해석 경계", y - 104)
    gap = 8
    col = (W - 2 * M - 2 * gap) / 3
    cards = [
        ("구조 감사  |  47/47", "현재 baseline 출력의 Citation ID 전수 해석", BLUE, LIGHT_BLUE),
        ("원문 표본  |  17/17", "두 기존 표본의 CPS PDF 정규화 원문 일치", GREEN, LIGHT_GREEN),
        ("해석 범위", "사람 의미판정 0쌍 · 외부 정확도 주장이 아님", ORANGE, LIGHT_ORANGE),
    ]
    for i, (title, body, accent, fill) in enumerate(cards):
        card(c, M + i * (col + gap), y, col, 82, title=title, body=body, fill=fill, accent=accent, title_size=8.0, body_size=6.3)
    callout(c, "<b>Gold Set 각주</b>  내부 구축 Gold Set 120질의는 CPS 원문 27페이지를 대조해 고정했다. Dev 29건에서만 파라미터를 선택하고 Test 91건은 한 번 평가했으며, 외부 전문가 평가 결과가 아니다.", y - 95, height=44, fill=LIGHT_RED, accent=RED)
    footer(c, f"검증일 {VERIFICATION_DATE} · 앱 {APP_VERSION} · Git {GIT_COMMIT} · 저장 구성점수 이후 가중합·순위 재현")
    c.save()


def final_page_9(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    header(c, "사업 발굴을 넘어, 근거의 생성·검토·감사를 반복업무로", "독창성 · 반복사용 가치 · 4단계 사업화 · 비용과 수익화 원칙")
    callout(c, "<b>차별화</b>  기존 사업 발굴이 ‘어디에 무엇을 할 것인가’를 제안했다면, K-ODA Compass는 ‘왜 판단했고, 어떤 원문이 지지하며, 무엇이 아직 가정인가’를 검토 가능한 단위로 제공한다.", 745, height=47, fill=LIGHT_ORANGE, accent=ORANGE)

    y = section_title(c, "1", "일반 서비스와 K-ODA Compass", 683)
    gap = 10
    col = (W - 2 * M - gap) / 2
    card(c, M, y, col, 125, title="일반 ODA 추천·생성 서비스", body="국가·분야 추천<br/>데이터 시각화<br/>생성형 문서작성", fill=LIGHT_BLUE, accent=BLUE, body_size=7.4, align=TA_CENTER)
    card(c, M + col + gap, y, col, 125, title="K-ODA Compass", body="7개 구성점수 · Page·Chunk ID · Evidence Class<br/>Citation · 설계가정 · 품질검사 · 5종 출력<br/>계보 감사 · 동일모델 통제평가 구조", fill=LIGHT_GREEN, accent=GREEN, body_size=6.9, align=TA_CENTER)

    y = section_title(c, "2", "반복업무 가치", y - 139)
    tasks = ["후보국 숏리스트", "분야 검토", "CPS 근거 수집", "내부 검토자료", "사업기획서 초안", "심사 질의 대응", "근거 갱신"]
    gap = 5
    col = (W - 2 * M - 6 * gap) / 7
    for i, task in enumerate(tasks):
        rect(c, M + i * (col + gap), y, col, 60, fill=[LIGHT_BLUE, LIGHT_GREEN, LIGHT_ORANGE][i % 3], stroke=BORDER)
        para(c, task, M + i * (col + gap) + 3, y - 19, col - 6, size=6.2, leading=7.8, color=TEXT, bold=True, align=TA_CENTER)

    y = section_title(c, "3", "4단계 사업화", y - 74)
    stages = [
        ("01  현재", "무료 공개 MVP", "사용자 유입<br/>실제 과업 검증<br/>공개 접근성", BLUE, LIGHT_BLUE),
        ("02  발표 전", "기술검증", "동일모델 반복실측<br/>OCR 보완<br/>점수 파이프라인 강화", GREEN, LIGHT_GREEN),
        ("03  90일", "외부 파일럿", "CSO·기업·지자체<br/>연구자·ODA 실무자<br/>성과지표 측정", ORANGE, LIGHT_ORANGE),
        ("04  향후", "기관형 워크스페이스", "조직 템플릿·권한<br/>검토이력·감사로그<br/>갱신·협업·승인", RED, LIGHT_RED),
    ]
    gap = 6
    col = (W - 2 * M - 3 * gap) / 4
    for i, (num, title, body, accent, fill) in enumerate(stages):
        x = M + i * (col + gap)
        rect(c, x, y, col, 125, fill=fill, stroke=BORDER)
        para(c, num, x + 5, y - 10, col - 10, size=6.5, leading=7.5, color=accent, bold=True, align=TA_CENTER)
        para(c, title, x + 5, y - 29, col - 10, size=8.0, leading=9.5, color=accent, bold=True, align=TA_CENTER)
        para(c, body, x + 7, y - 57, col - 14, size=6.2, leading=8.1, color=TEXT, align=TA_CENTER)

    y = section_title(c, "4", "비용구조와 수익화 원칙", y - 139)
    data = [
        ["운영비용", "무료 공개 기능", "기관형 전환 조건"],
        ["공공데이터 수집·정합화", "국가·분야 탐색·기본 Score", "기관별 데이터·정기 갱신"],
        ["CPS OCR·인덱싱", "공개 범위 원문검색·Evidence Pack", "조직 문서·권한형 검색"],
        ["선택적 LLM·저장·배포", "Local RAG·공개 다운로드", "협업·감사·승인·보관"],
        ["품질검사·유지관리", "기본 Citation·한계 표시", "파일럿 사용성·지불의사 확인 후 전환"],
    ]
    y = table_flowable(c, data, M + 18, y, [165, 170, 166], font_size=6.3, leading=8.2, row_fills=[WHITE, LIGHT_BLUE], alignments=["LEFT", "LEFT", "LEFT"], cell_padding=3.6)
    callout(c, "<b>사업화 원칙</b>  데이터 접근성과 기본 검증 기능은 무료로 유지하고, 반복 운영비가 발생하는 기관형 협업·감사·갱신 기능은 파일럿에서 사용성과 지불의사를 확인한 뒤 제공한다.", y - 17, height=47, fill=LIGHT_ORANGE, accent=ORANGE)
    footer(c, "현재: 공개 MVP · 다음: 기술검증 → 90일 외부 파일럿 → 수요·비용 검증 후 기관형 워크스페이스")
    c.save()


def final_page_10(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    header(c, "90일 안에 기술검증·사용자성과·기관적용 가능성을 측정한다", "실행계획 · 측정 KPI · 책임 있는 AI · 공개 Demo와 Repository")
    callout(c, "<b>실행 원칙</b>  기술기능을 더 붙이는 것이 목적이 아니다. 검색·점수·Citation·생성계층의 검증을 고정하고, 실제 사용자의 과업성과와 기관 운영조건을 순차적으로 측정한다.", 745, height=43)

    y = section_title(c, "1", "수상 후 90일 실행계획", 688)
    gap = 8
    col = (W - 2 * M - 2 * gap) / 3
    timeline = [
        ("0–30일  |  기술검증", "동일모델 A/B/C 반복실측<br/>OCR 우선 문서 보완<br/>점수 상류 파이프라인 강화<br/>회귀 QA 자동화", BLUE, LIGHT_BLUE),
        ("31–60일  |  사용자성과", "외부 사용자 실증<br/>추천타당성·문서작성시간<br/>근거확인시간·Citation 오류<br/>과업성공률 측정", GREEN, LIGHT_GREEN),
        ("61–90일  |  기관적용", "워크스페이스·감사로그<br/>기관형 요구사항<br/>운영비·지불의사<br/>유지관리 구조 검증", ORANGE, LIGHT_ORANGE),
    ]
    for i, (title, body, accent, fill) in enumerate(timeline):
        card(c, M + i * (col + gap), y, col, 132, title=title, body=body, fill=fill, accent=accent, title_size=8.4, body_size=6.6)

    y = section_title(c, "2", "책임 있는 AI 원칙", y - 146)
    principles = [
        "Human-in-the-loop", "자동 정책결정 금지", "근거·가정 분리", "원문 Citation",
        "미확인 정보 표시", "검색·생성 계층 분리", "Local RAG 접근성", "상용모델 종속 최소화",
        "오류·한계 공개", "중소 CSO 접근비용 절감",
    ]
    gap = 6
    col = (W - 2 * M - 4 * gap) / 5
    for i, label in enumerate(principles):
        row, pos = divmod(i, 5)
        rect(c, M + pos * (col + gap), y - row * 54, col, 46, fill=[LIGHT_BLUE, LIGHT_GREEN, LIGHT_ORANGE, LIGHT_RED, LIGHT_BLUE][pos], stroke=BORDER)
        para(c, label, M + pos * (col + gap) + 4, y - row * 54 - 16, col - 8, size=6.2, leading=7.6, color=[BLUE, GREEN, ORANGE, RED, BLUE][pos], bold=True, align=TA_CENTER)

    y = section_title(c, "3", "공개 실행경로", y - 114)
    gap = 14
    col = (W - 2 * M - gap) / 2
    for i, (title, url, accent, fill) in enumerate([("LIVE DEMO", LIVE_URL, BLUE, LIGHT_BLUE), ("OPEN REPOSITORY", GITHUB_URL, GREEN, LIGHT_GREEN)]):
        x = M + i * (col + gap)
        rect(c, x, y, col, 122, fill=fill, stroke=BORDER)
        para(c, title, x + 8, y - 12, col - 94, size=9.0, leading=10.5, color=accent, bold=True)
        para(c, url, x + 8, y - 36, col - 94, size=5.8, leading=7.2, color=TEXT)
        para(c, "실제 서비스" if i == 0 else "코드·검증자료", x + 8, y - 61, col - 94, size=6.5, leading=8.0, color=MUTED, bold=True)
        draw_qr(c, url, x + col - 84, y - 94, 74)
        c.linkURL(url, (x, y - 122, x + col, y), relative=0)

    y = section_title(c, "4", "최종 결론", y - 136)
    callout(c, "<b>K-ODA Compass는 생성형 AI를 덧붙인 대시보드가 아니다.</b>  외교·ODA 공공데이터를 점수·검색·근거·Citation·가정·출력으로 분해하고 각 계층을 검증·감사할 수 있게 만든 공공 AI 근거 운영체계다.", y, height=61, fill=LIGHT_ORANGE, accent=ORANGE)
    footer(c, f"Live Demo: {LIVE_URL}  ·  GitHub: {GITHUB_URL}")
    c.linkURL(LIVE_URL, (M, 20, 270, 38), relative=0)
    c.linkURL(GITHUB_URL, (270, 20, W - M, 38), relative=0)
    c.save()


def correction_overlay(page_number: int, path: Path) -> None:
    """Create evidence-backed wording and alignment corrections for preserved pages."""
    c = canvas.Canvas(str(path), pagesize=A4)
    if page_number == 1:
        c.setFillColor(WHITE)
        c.setStrokeColor(WHITE)
        c.rect(414, 551, 85, 15, fill=1, stroke=0)
        para(c, "pytest 54 passed", 416, 564, 80, size=6.2, leading=7.5, color=MUTED, align=TA_CENTER)
    elif page_number == 3:
        rect(c, M, 715, W - 2 * M, 42, fill=LIGHT_BLUE, stroke=BORDER)
        c.setFillColor(BLUE)
        c.rect(M, 673, 2.5, 42, fill=1, stroke=0)
        para(
            c,
            "<b>현재 직접 활용 구조:</b> 구조화 데이터 3개 그룹과 비정형 CPS 문서 1개 그룹을 국가·분야 기준으로 연결한다.",
            M + 9,
            704,
            W - 2 * M - 18,
            size=8.2,
            leading=11.2,
            color=TEXT,
        )
    elif page_number == 4:
        c.setFillColor(WHITE)
        c.setStrokeColor(WHITE)
        c.rect(M - 2, 610, W - 2 * M + 4, 110, fill=1, stroke=0)
        para(c, "1. 데이터 처리 구조와 현재 재현 경계", M, 711, W - 2 * M, size=10.6, leading=13.2, color=NAVY, bold=True)
        # Redraw both pipelines so box heights, baselines and arrows are aligned.
        rect(c, M, 691, W - 2 * M, 81, fill=LIGHT_GRAY, stroke=BORDER)
        para(c, "구조화 데이터 파이프라인", M + 4, 682, 180, size=8.4, leading=10.0, color=BLUE, bold=True)
        labels = [
            "원자료·외부 데이터",
            "출처·기준연도 기록",
            "국가명·ISO3 / 분야코드 정합화",
            "정합화된 국가·분야 분석 테이블",
            "저장된 7개 구성점수",
            "가중합 Opportunity Score",
        ]
        widths = [72, 75, 102, 91, 75, 91]
        x = M + 4
        for i, (label, width) in enumerate(zip(labels, widths)):
            rect(c, x, 663, width, 47, fill=[LIGHT_BLUE, LIGHT_BLUE, LIGHT_GREEN, LIGHT_BLUE, LIGHT_ORANGE, LIGHT_BLUE][i], stroke=BORDER)
            para(c, label, x + 3, 646, width - 6, size=5.2, leading=6.5, color=[BLUE, BLUE, GREEN, BLUE, ORANGE, NAVY][i], bold=True, align=TA_CENTER)
            x += width
            if i < len(labels) - 1:
                para(c, "→", x, 644, 5, size=6.6, leading=7.0, color=BLUE, bold=True, align=TA_CENTER)
                x += 5

        rect(c, M, 610, W - 2 * M, 58, fill=WHITE, stroke=BORDER)
        para(c, "CPS 문서 파이프라인", M + 4, 602, 160, size=8.4, leading=10.0, color=GREEN, bold=True)
        cps_labels = [
            "CPS PDF",
            "페이지 텍스트·Chunk ID",
            "국가·분야 필터",
            "Lexical·Embedding 후보검색",
            "Hybrid 결합",
            "Evidence Class",
            "Citation 후보",
        ]
        cps_widths = [50, 71, 66, 87, 58, 69, 64]
        x = M + 4
        for i, (label, width) in enumerate(zip(cps_labels, cps_widths)):
            rect(c, x, 587, width, 35, fill=[LIGHT_BLUE, LIGHT_GREEN, LIGHT_BLUE, LIGHT_ORANGE, LIGHT_GREEN, LIGHT_BLUE, LIGHT_ORANGE][i], stroke=BORDER)
            para(c, label, x + 2, 575, width - 4, size=5.0, leading=6.1, color=[NAVY, GREEN, BLUE, ORANGE, GREEN, BLUE, ORANGE][i], bold=True, align=TA_CENTER)
            x += width
            if i < len(cps_labels) - 1:
                para(c, "→", x, 572, 11, size=6.4, leading=7.0, color=GREEN, bold=True, align=TA_CENTER)
                x += 11

        rect(c, M, 550, W - 2 * M, 39, fill=LIGHT_ORANGE, stroke=BORDER)
        para(
            c,
            "<b>운영 선택</b>  K-ODA Compass는 검색방식을 일률적으로 채택하지 않는다. Lexical·Embedding·Hybrid·Filtered Hybrid를 독립 Test Set에서 비교한 결과, 현재 CPS 문서에서 Recall@5와 지연시간이 가장 우수한 Lexical을 운영 기본값으로 채택했다. Embedding은 lazy loading하며 실패 시 Lexical로 fallback한다.",
            M + 7,
            542,
            W - 2 * M - 14,
            size=5.45,
            leading=6.7,
            color=TEXT,
        )
        rect(c, 382, 191, 169, 55, fill=LIGHT_ORANGE, stroke=BORDER)
        para(c, "현재 검색 검증", 390, 179, 153, size=7.5, leading=9.0, color=ORANGE, bold=True, align=TA_CENTER)
        para(c, "120개 동결 질의 비교 완료<br/>앱 기본 lexical · filtered benchmark", 391, 159, 151, size=5.7, leading=7.3, color=TEXT, align=TA_CENTER)
    elif page_number == 5:
        c.setFillColor(WHITE)
        c.setStrokeColor(WHITE)
        c.rect(28, 690, 540, 116, fill=1, stroke=0)
        para(c, "사용자는 세 단계만으로 국가·분야·사업근거를 연결한다", M, 797, W - 2 * M, size=17.0, leading=20.0, color=NAVY, bold=True)
        para(c, "르완다 × 기술·환경·에너지 실제 작동 서비스 흐름", M, 773, W - 2 * M, size=9.0, leading=11.0, color=MUTED, bold=True)
        summary = [("대상 국가", "르완다", BLUE, LIGHT_BLUE), ("사업 분야", "기술·환경·에너지", GREEN, LIGHT_GREEN), ("Opportunity Score", "65.28 · 전체 2위", ORANGE, LIGHT_ORANGE), ("근거 범위", "태그 15 · 직접 4", ORANGE, colors.HexColor("#FFF8E6"))]
        gap = 0
        width = (W - 2 * M) / 4
        for i, (label, value, accent, fill) in enumerate(summary):
            x = M + i * width
            rect(c, x, 748, width, 49, fill=fill, stroke=BORDER)
            para(c, label, x + 5, 739, width - 10, size=5.8, leading=6.8, color=accent, bold=True, align=TA_CENTER)
            para(c, value, x + 5, 720, width - 10, size=7.1, leading=8.3, color=TEXT, bold=True, align=TA_CENTER)
        c.rect(28, 666, 540, 30, fill=1, stroke=0)
        para(c, "현재 앱에서 동일 조건이 이어지는 3단계", M, 690, W - 2 * M, size=10.6, leading=13.2, color=NAVY, bold=True)
        c.rect(38, 620, 520, 48, fill=1, stroke=0)
        x_positions = [40, 213, 386]
        titles = ["01  후보국 우선검토", "02  분야 우선검토", "03  AI Builder"]
        bodies = [
            "50개국 순위 · 구성점수 기여도<br/>#2 르완다 · 65.28 · 데이터 신뢰도",
            "기술·환경·에너지<br/>협력기반·정책정합 · 태그 청크 풀 15건",
            "검색·CPS·Evidence Pack<br/>Citation·설계가정·5종 출력",
        ]
        fills = [LIGHT_BLUE, LIGHT_GREEN, LIGHT_ORANGE]
        accents = [BLUE, GREEN, ORANGE]
        for i, x in enumerate(x_positions):
            rect(c, x, 668, 157, 48, fill=fills[i], stroke=BORDER)
            para(c, titles[i], x + 6, 657, 145, size=7.8, leading=9.3, color=accents[i], bold=True, align=TA_CENTER)
            para(c, bodies[i], x + 7, 637, 143, size=5.5, leading=7.0, color=TEXT, align=TA_CENTER)
            if i < 2:
                para(c, "→", x + 159, 637, 12, size=10.5, leading=11.5, color=BLUE, bold=True, align=TA_CENTER)
        c.setFillColor(WHITE)
        c.setStrokeColor(WHITE)
        c.rect(28, 598, 540, 22, fill=1, stroke=0)
        para(c, "STEP 1. 후보국에서 르완다를 선택", M, 614, W - 2 * M, size=9.6, leading=11.5, color=BLUE, bold=True)
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
        c.setFillColor(WHITE)
        c.setStrokeColor(WHITE)
        c.rect(28, 696, 540, 53, fill=1, stroke=0)
        rect(c, M, 745, W - 2 * M, 43, fill=LIGHT_BLUE, stroke=BORDER)
        para(c, "<b>Evidence Pack First</b>  Direct Evidence · Supporting Evidence · Design Assumption · Further Research를 먼저 구분하고, A01~A07 설계가정을 사실과 분리한 뒤 문서를 생성한다.", M + 9, 736, W - 2 * M - 18, size=6.6, leading=8.8, color=TEXT)

        c.rect(28, 580, 540, 116, fill=1, stroke=0)
        para(c, "1. Evidence Pack First 처리 순서", M, 690, W - 2 * M, size=10.6, leading=13.2, color=NAVY, bold=True)
        flow = ["사용자<br/>요청", "Score<br/>Context", "CPS<br/>검색", "Evidence<br/>Pack", "Citation", "설계가정<br/>A01~A07", "문서<br/>생성", "품질<br/>검사"]
        gap = 5
        col = (W - 2 * M - 7 * gap) / 8
        for i, label in enumerate(flow):
            x = M + i * (col + gap)
            rect(c, x, 670, col, 77, fill=[LIGHT_BLUE, LIGHT_GREEN, LIGHT_ORANGE][i % 3], stroke=BORDER)
            para(c, f"0{i + 1}", x + 3, 659, col - 6, size=5.6, leading=6.5, color=[BLUE, GREEN, ORANGE][i % 3], bold=True, align=TA_CENTER)
            para(c, label, x + 3, 636, col - 6, size=5.8, leading=7.2, color=TEXT, bold=True, align=TA_CENTER)
            if i < 7:
                para(c, "→", x + col, 632, gap, size=6.4, leading=7, color=BLUE, bold=True, align=TA_CENTER)

        c.rect(38, 500, 520, 84, fill=1, stroke=0)
        para(c, "2. 생성되는 산출물과 Evidence Class", M, 579, W - 2 * M, size=10.6, leading=13.2, color=NAVY, bold=True)
        output_cards = [
            ("사업기획서", "국가선정 근거·문제정의·목표·활동·위험·성과지표 후보", BLUE, LIGHT_BLUE),
            ("핵심 Brief", "핵심 사업개념·선정근거·추가 검토사항을 요약", GREEN, LIGHT_GREEN),
            ("Evidence Pack", "Evidence ID·출처유형·직접성·문서명·페이지·분야", ORANGE, LIGHT_ORANGE),
            ("PDF 출력", "Proposal·Brief를 A4 문서로 생성해 검토·회의에 활용", ORANGE, colors.HexColor("#FFF8E6")),
        ]
        x_positions = [39, 168.5, 298, 427.5]
        for x, (title, body, accent, fill) in zip(x_positions, output_cards):
            rect(c, x, 558, 129.5, 56, fill=fill, stroke=BORDER)
            para(c, title, x + 5, 545, 119.5, size=8.0, leading=9.6, color=accent, bold=True, align=TA_CENTER)
            para(c, body, x + 6, 520, 117.5, size=5.1, leading=6.4, color=TEXT, align=TA_CENTER)

        # Replace the legacy button label embedded in both screenshots.
        for x in (172, 439):
            rect(c, x, 412, 53, 10, fill=WHITE, stroke=colors.HexColor("#DCE2E8"), line_width=0.3)
            para(c, "Brief MD", x + 2, 409.5, 49, size=3.8, leading=4.4, color=TEXT, align=TA_CENTER)
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
        if page_number in generated_pages:
            source = generated_pages[page_number]
        else:
            source = SOURCE_DIR / f"{page_number}.pdf"
        if page_number in {5, 6}:
            source = INTERMEDIATE_DIR / f"rasterized_source_{page_number}.pdf"
            rasterized_source_page(page_number, source)
        if not source.exists():
            raise FileNotFoundError(source)
        page = PdfReader(str(source)).pages[0]

        if page_number in {5, 6}:
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
        1: INTERMEDIATE_DIR / "page_01.pdf",
        2: INTERMEDIATE_DIR / "page_02.pdf",
        3: INTERMEDIATE_DIR / "page_03.pdf",
        4: INTERMEDIATE_DIR / "page_04.pdf",
        7: INTERMEDIATE_DIR / "page_07.pdf",
        8: INTERMEDIATE_DIR / "page_08.pdf",
        9: INTERMEDIATE_DIR / "page_09.pdf",
        10: INTERMEDIATE_DIR / "page_10.pdf",
    }
    page_1(generated_pages[1])
    page_2(generated_pages[2])
    page_3(generated_pages[3])
    page_4(generated_pages[4])
    final_page_7(generated_pages[7])
    final_page_8(generated_pages[8])
    final_page_9(generated_pages[9])
    final_page_10(generated_pages[10])
    merge_pdf(generated_pages)
    print(FINAL_PDF)


if __name__ == "__main__":
    main()
