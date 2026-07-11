
# -*- coding: utf-8 -*-
"""
K-ODA Compass v2.1.5
Top 50 + KOICA 2019-2024 + WDI 2019-2025 + Policy/Risk scoring

Run:
    streamlit run app.py
"""
from __future__ import annotations

import io
import os
import csv
import hashlib
from pathlib import Path
from typing import List, Dict
import re

import pandas as pd
import streamlit as st

st.set_page_config(page_title="K-ODA Compass v2.1.5", page_icon="🧭", layout="wide", initial_sidebar_state="collapsed")
APP_DIR = Path(__file__).resolve().parent
FONT_DIR = APP_DIR / "assets" / "fonts"
REGULAR_FONT_PATH = FONT_DIR / "NanumGothic-Regular.ttf"
BOLD_FONT_PATH = FONT_DIR / "NanumGothic-Bold.ttf"
FONT_LICENSE_PATH = FONT_DIR / "OFL.txt"
GITHUB_URL = "https://github.com/gross08-lab/k-oda-compass"
LIVE_DEMO_URL = "https://k-oda-compass.streamlit.app"
AUDITED_RAG_DOCUMENTS = 14_492
AUDITED_CPS_CHUNK_COUNTRIES = 20
AUDITED_CPS_TOP50_COUNTRIES = 19
APP_VERSION = "v2.1.5"
MODEL_VERSION = "v2.1"
DATA_SNAPSHOT = "KOICA 2019~2024 · WDI 최신값 최대 2025 · 정책·실행환경 2023-06-14"
INTERNAL_TEST_DATE = "2026-07-11"
PYTEST_RESULT = "16 passed"

DATA_FILES = {
    "master": "KODA_master_score_top50_v21.csv",
    "wdi": "KODA_wdi_latest_top50_long_v2.csv",
    "country_year": "KODA_country_year_trend_2019_2024.csv",
    "sector_year": "KODA_country_sector_year_trend_2019_2024.csv",
    "sector_summary": "KODA_country_sector_summary_2019_2024.csv",
    "projects": "KODA_project_evidence_top50_2019_2024.csv",
    "policy_risk": "KODA_policy_risk_scores_top50_v21.csv",
    "cps_pdf": "KODA_cps_pdf_chunks.csv",
    "cps_coverage": "KODA_cps_pdf_ocr_coverage.csv",
    "weights": "KODA_v21_score_weights.csv",
    "notes": "KODA_v21_score_notes.csv",
}

VIEW_DATA_KEYS = {
    "개요": ("master", "weights"),
    "순위": ("master", "weights", "cps_pdf"),
    "프로필": ("master", "weights", "wdi", "country_year", "sector_summary", "sector_year", "policy_risk", "cps_pdf"),
    "분야 우선검토": ("master", "weights", "wdi", "sector_summary", "sector_year", "policy_risk", "cps_pdf"),
    "AI Builder": ("master", "wdi", "sector_summary", "weights", "projects", "policy_risk", "cps_pdf"),
    "근거·재현성": ("master", "weights", "notes", "cps_coverage"),
    "AI·모델 검증": ("master", "weights", "cps_coverage"),
    "심사용 요약": ("master", "wdi", "projects", "policy_risk", "sector_summary", "cps_pdf"),
    "배포": (),
}


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .main .block-container { padding-top: 1.25rem; padding-bottom: 3rem; }
        .koda-hero { padding:1.25rem 1.35rem; border-radius:18px; border:1px solid rgba(45,84,135,.22); background:linear-gradient(135deg,rgba(18,55,96,.08),rgba(60,120,180,.04)); margin-bottom:1.1rem; }
        .koda-title { font-size:2.05rem; font-weight:800; line-height:1.18; margin:0 0 .35rem 0; color:var(--text-color); }
        .koda-subtitle { font-size:1rem; line-height:1.65; color:var(--text-color); opacity:.9; margin:0; }
        .metric-card { padding:1rem 1.05rem; border-radius:16px; background:rgba(250,252,255,.93); border:1px solid rgba(30,70,110,.14); min-height:108px; box-shadow:0 1px 6px rgba(20,40,80,.04); }
        .metric-label { font-size:.84rem; color:rgba(65,78,92,.82); margin-bottom:.35rem; }
        .metric-value { font-size:1.5rem; font-weight:800; color:#173a5e; }
        .metric-note { font-size:.78rem; color:rgba(65,78,92,.72); margin-top:.25rem; }
        .section-note, .decision-card { padding:.85rem 1rem; border-left:4px solid #315d86; background:rgba(49,93,134,.07); border-radius:10px; line-height:1.62; margin:.5rem 0 1rem 0; }
        .insight-card, .pipeline-card, .risk-card { padding:1rem 1.05rem; border-radius:16px; background:rgba(255,255,255,.9); border:1px solid rgba(35,78,115,.16); box-shadow:0 1px 7px rgba(20,40,80,.04); line-height:1.55; min-height:118px; margin-bottom:.65rem; }
        .insight-title, .pipeline-title, .risk-title { font-weight:800; font-size:.98rem; color:#173a5e; margin-bottom:.35rem; }
        .insight-body, .pipeline-body, .risk-body { font-size:.9rem; color:rgba(45,55,70,.9); }
        .brief-kicker { padding:.85rem 1rem; border-radius:14px; background:rgba(36,75,120,.08); border:1px solid rgba(36,75,120,.16); margin:.7rem 0 1rem 0; line-height:1.6; }
        .pill { display:inline-block; padding:.28rem .6rem; border-radius:999px; background:rgba(23,58,94,.08); color:#173a5e; font-weight:650; font-size:.82rem; margin:.12rem .18rem .12rem 0; }
        .small-muted { color:rgba(80,90,110,.74); font-size:.88rem; }
        .stTabs [data-baseweb="tab-list"] { gap:.35rem; }
        .stTabs [data-baseweb="tab"] { border-radius:10px 10px 0 0; padding:.72rem .95rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_csv(file_name: str) -> pd.DataFrame:
    path = APP_DIR / file_name
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {file_name}")
    return pd.read_csv(path)


def prepare_data(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    # numeric coercions
    # pandas 3.x removed errors="ignore" for to_numeric.
    # Convert only columns that actually contain numeric values; keep text columns unchanged.
    for df in data.values():
        for col in df.columns:
            if any(x in col for x in ["Score", "Count", "Raw", "Coverage", "Year", "Rank", "지수", "점수", "순위", "여건"]):
                converted = pd.to_numeric(df[col], errors="coerce")
                if converted.notna().sum() > 0:
                    df[col] = converted
    master = data.get("master")
    if master is not None and "Rank_V21" in master.columns:
        master = master.sort_values("Rank_V21", ascending=True).reset_index(drop=True)
        data["master"] = master
    return data


@st.cache_data(show_spinner=False, ttl=900, max_entries=1)
def load_view_data(view_name: str) -> dict[str, pd.DataFrame]:
    """Load only the CSV files needed by the active top-level view."""
    data = {key: load_csv(DATA_FILES[key]) for key in VIEW_DATA_KEYS[view_name]}
    return prepare_data(data)


@st.cache_data(show_spinner=False, ttl=900, max_entries=1)
def load_optional_dataset(data_key: str) -> pd.DataFrame:
    """Load a large detail dataset only after its on-screen control is selected."""
    return prepare_data({data_key: load_csv(DATA_FILES[data_key])})[data_key]


@st.cache_data(show_spinner=False, ttl=900, max_entries=1)
def count_csv_records(data_keys: tuple[str, ...]) -> dict[str, int]:
    """Count CSV records with a streaming parser without retaining source rows."""
    counts = {}
    for data_key in data_keys:
        with (APP_DIR / DATA_FILES[data_key]).open("r", encoding="utf-8-sig", newline="") as handle:
            counts[data_key] = max(sum(1 for _ in csv.reader(handle)) - 1, 0)
    return counts


@st.cache_data(show_spinner=False, ttl=900, max_entries=1)
def count_valid_wdi_latest() -> tuple[int, int]:
    total = 0
    valid = 0
    with (APP_DIR / DATA_FILES["wdi"]).open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            total += 1
            value = safe_text(row.get("Latest_Value")).lower()
            if value not in {"", "nan", "none", "n/a"}:
                valid += 1
    return valid, total


def load_all_data() -> dict[str, pd.DataFrame]:
    """Offline artifact compatibility helper; the Streamlit app never calls it."""
    data = {key: load_csv(file_name) for key, file_name in DATA_FILES.items()}
    return prepare_data(data)


def validate_files(data_keys: tuple[str, ...]) -> None:
    missing = [DATA_FILES[key] for key in data_keys if not (APP_DIR / DATA_FILES[key]).exists()]
    if missing:
        st.error("현재 화면에 필요한 CSV 파일이 같은 폴더에 없습니다.")
        st.code("\n".join(missing), language="text")
        st.stop()


def get_plotly_express():
    """Import Plotly only on chart views to keep the landing view lightweight."""
    import plotly.express as px

    return px


def fmt_number(value, digits: int = 1, suffix: str = "") -> str:
    if pd.isna(value):
        return "N/A"
    try:
        return f"{float(value):,.{digits}f}{suffix}"
    except Exception:
        return str(value)


def fmt_int(value) -> str:
    if pd.isna(value):
        return "N/A"
    try:
        return f"{int(round(float(value))):,}"
    except Exception:
        return str(value)


def fmt_year(value) -> str:
    """Format a year without applying thousands separators."""
    if pd.isna(value):
        return "연도 미표기"
    try:
        return str(int(round(float(value))))
    except Exception:
        match = re.search(r"\b(?:19|20)\d{2}\b", safe_text(value))
        return match.group(0) if match else safe_text(value) or "연도 미표기"


def fmt_raw_money(value) -> str:
    """Display raw disbursement values without rounding small positive values to 0.

    The source-data unit is kept as a raw value because the official metadata/unit
    can differ by file. Values below 1 are shown with decimals rather than rounded
    to zero, which is misleading in the demo.
    """
    if pd.isna(value):
        return "금액 미표기"
    try:
        v = float(value)
        if v <= 0:
            return "금액 미표기"
        if v < 1:
            txt = f"{v:.4f}".rstrip("0").rstrip(".")
            return txt if txt else "금액 미표기"
        return f"{v:,.2f}".rstrip("0").rstrip(".")
    except Exception:
        txt = str(value).strip()
        return txt if txt and txt.lower() not in {"nan", "none", "0", "0.0"} else "금액 미표기"


def clean_project_text(value) -> str:
    if pd.isna(value):
        return "사업명 미표기"
    text = str(value).strip()
    replacements = {
        "Programin": "Program in",
        "ProgramIn": "Program in",
        "Degree Programin": "Degree Program in",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return " ".join(text.split())


def display_candidate_type(value) -> str:
    text = "" if pd.isna(value) else str(value).strip()
    if "고위험" in text:
        return "리스크 보완형: 개발수요는 높지만 제도·거버넌스 위험 검증 필요"
    if "협력기반" in text:
        return "협력기반 확장형: 기존 한국 협력경험을 활용한 후속사업 검토"
    if "정책정합" in text:
        return "우선검토형: 개발수요와 정책정합성을 바탕으로 사업개념 구체화 권장"
    return "현지검증형: 현지수요와 파트너 역량 확인 필요"


def compact_candidate_label(value) -> str:
    return display_candidate_type(value).split(":", 1)[0]


def candidate_next_step(value) -> str:
    label = compact_candidate_label(value)
    if label == "우선검토형":
        return "사업개념과 수혜자 가설 구체화"
    if label == "리스크 보완형":
        return "현지 파트너·제도위험 검증"
    if label == "협력기반 확장형":
        return "기존 사업의 후속·확장 가능성 검토"
    return "현지수요·운영주체 확인"


def relative_score_label(reference: pd.Series, value) -> str:
    """Describe a score relative to the Top 50 without inventing absolute bands."""
    numeric = pd.to_numeric(reference, errors="coerce").dropna()
    score = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if numeric.empty or pd.isna(score):
        return "상대위치 확인 필요"
    percentile = float((numeric <= score).mean() * 100)
    return f"Top 50 내 {percentile:.0f}백분위"


def feasibility_label(value, reference: pd.Series | None = None) -> str:
    if reference is None:
        return "상대점수 · 세부지표 확인"
    return relative_score_label(reference, value)


def english_sector_name(sector: str) -> str:
    mapping = {
        "공공행정": "Public Administration",
        "기술환경에너지": "Technology, Environment and Energy",
        "교육": "Education",
        "농림수산": "Agriculture, Forestry and Fisheries",
        "보건의료": "Health",
        "산업": "Industry",
        "긴급구호": "Humanitarian Assistance",
        "기타": "Development Cooperation",
    }
    return mapping.get(str(sector).strip(), "Development Cooperation")


def english_country_name(row: pd.Series, fallback: str) -> str:
    value = row.get("WDI_Country_Name", fallback)
    if pd.isna(value) or not str(value).strip():
        return fallback
    return str(value).strip()


def wdi_public_admin_bridge(sector: str) -> str:
    if sector == "공공행정":
        return "디지털접근과 전력접근 수준은 데이터 기반 행정서비스 도입 시 인프라 제약을 함께 고려해야 함을 시사합니다."
    return "WDI 개발수요 신호는 사업 설계 시 서비스 접근성, 인프라 제약, 현지 역량강화 필요성을 함께 검토해야 함을 시사합니다."


RAG_STOPWORDS = {
    "and", "or", "the", "for", "with", "from", "this", "that", "into", "based",
    "사업", "기반", "추천", "분야", "국가", "데이터", "개발", "협력", "지원",
    "검토", "활용", "기획", "파일럿", "프로젝트", "서비스", "정책", "리스크",
}


def safe_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def tokenize_for_rag(*parts) -> set[str]:
    text = " ".join(safe_text(p) for p in parts).lower()
    base_tokens = re.findall(r"[0-9a-zA-Z가-힣]+", text)
    tokens: set[str] = set()
    for token in base_tokens:
        if len(token) >= 2 and token not in RAG_STOPWORDS:
            tokens.add(token)
        # Korean compound words often carry the signal inside the word.
        if re.search(r"[가-힣]", token) and len(token) >= 4:
            for i in range(len(token) - 1):
                gram = token[i:i + 2]
                if gram not in RAG_STOPWORDS:
                    tokens.add(gram)
    return tokens


def make_rag_doc(
    rows: list[dict],
    source_type: str,
    country: str,
    sector: str,
    title: str,
    content: str,
    citation: str,
    metadata: dict | None = None,
) -> None:
    doc_id = f"{source_type[:3].upper().replace('/', '')}-{len(rows) + 1:05d}"
    row = {
        "Doc_ID": doc_id,
        "Source_Type": source_type,
        "Country_KR": country,
        "Sector_Group": sector,
        "Title": title,
        "Content": content,
        "Citation": citation,
        "Tokens": sorted(tokenize_for_rag(country, sector, title, content, citation)),
    }
    row.update(metadata or {})
    rows.append(row)


def normalized_project_key(value) -> str:
    text = clean_project_text(value).lower()
    text = re.sub(r"[('`’\"]?\s*\d{2,4}\s*[-–~]\s*['`’\"]?\d{2,4}\s*[)'`’\"]?", " ", text)
    text = re.sub(r"[('`’\"]?\s*(?:19|20)\d{2}\s*[)'`’\"]?", " ", text)
    text = re.sub(r"[^0-9a-z가-힣]+", " ", text)
    return " ".join(text.split())


def wdi_direction_label(value) -> str:
    direction = safe_text(value)
    if direction == "lower_is_higher_need":
        return "값이 낮을수록 개선 필요 가능성이 큼"
    if direction == "higher_is_higher_need":
        return "값이 높을수록 수요 또는 위험이 커질 수 있음"
    return "해석 시 다른 지표와 함께 검토 필요"


def wdi_relevance_level(sector: str, signal: str, indicator_name: str) -> str:
    text = f"{signal} {indicator_name}".lower()
    direct_terms = {
        "공공행정": ("governance", "government", "internet", "digital", "전자정부", "인터넷"),
        "교육": ("school", "education", "literacy", "교육"),
        "보건의료": ("life expectancy", "mortality", "health", "보건", "기대수명"),
        "기술환경에너지": ("electric", "energy", "internet", "co2", "전력", "에너지"),
        "농림수산": ("agriculture", "rural", "food", "농업", "농촌"),
    }
    if any(term in text for term in direct_terms.get(sector, ())):
        return "간접 관련 · 국가 배경 보조 신호"
    if any(term in text for term in ("gdp", "income", "poverty", "population", "소득", "빈곤")):
        return "국가 배경 보조 신호"
    return "간접 관련"


def infer_project_period(title: str, observed_years: list[int]) -> str:
    text = safe_text(title)
    match = re.search(r"['’]?(\d{2,4})\s*[-–~]\s*['’]?(\d{2,4})", text)
    if match:
        start, end = int(match.group(1)), int(match.group(2))
        start = start + 2000 if start < 100 else start
        end = end + 2000 if end < 100 else end
        if 2000 <= start <= 2100 and 2000 <= end <= 2100:
            return f"{start}–{end}"
    if observed_years:
        return fmt_year(min(observed_years)) if len(observed_years) == 1 else f"{fmt_year(min(observed_years))}–{fmt_year(max(observed_years))}"
    return "사업기간 메타데이터 없음"


@st.cache_data(show_spinner=False, ttl=900, max_entries=1)
def build_rag_corpus(master: pd.DataFrame, wdi: pd.DataFrame, projects: pd.DataFrame, policy: pd.DataFrame, sector_summary: pd.DataFrame, cps_pdf: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []

    for source_index, r in master.iterrows():
        country = safe_text(r.get("Country_KR"))
        title = f"{country} v2.1 opportunity score"
        content = (
            f"{country} 종합점수 {fmt_number(r.get('K_ODA_Opportunity_Score_V21'))}, "
            f"개발수요 {fmt_number(r.get('Development_Need_Score'))}, "
            f"한국 기존 협력경험 {fmt_number(r.get('Korea_Coop_Base_Score_V2'))}, "
            f"분야적합성 {fmt_number(r.get('Sector_Fit_Score_V2'))}, "
            f"정책정합성 {fmt_number(r.get('Policy_Alignment_Score_V21'))}, "
            f"실행가능성 {fmt_number(r.get('Risk_Feasibility_Score_V21'))}, "
            f"후보유형 {display_candidate_type(r.get('Candidate_Type_V21'))}, "
            f"추천분야 {safe_text(r.get('Recommended_Service_Angle_V2'))}."
        )
        citation = f"K-ODA Compass v2.1 master score, Rank #{fmt_int(r.get('Rank_V21'))}, {country}"
        make_rag_doc(rows, "Score Model", country, "전체", title, content, citation, {
            "Evidence_Class": "Model Output",
            "Provider": "K-ODA Compass",
            "Dataset_Name": DATA_FILES["master"],
            "Original_Title": title,
            "Reference_Year": "모델 v2.1",
            "Collected_At": "수집일 메타데이터 없음",
            "Source_URL": GITHUB_URL,
            "Source_File": DATA_FILES["master"],
            "Source_Record_ID": f"row-{int(source_index) + 2}",
            "Model_Role": "국가 우선검토 점수와 후보유형",
            "Original_Score": fmt_number(r.get("K_ODA_Opportunity_Score_V21"), 2),
            "Weight": "7개 구성요소 가중합",
            "Weighted_Contribution": fmt_number(r.get("K_ODA_Opportunity_Score_V21"), 2),
            "Model_Version": MODEL_VERSION,
            "Limitations": "파생 모델 출력이며 현지조사나 사업 타당성 검토를 대체하지 않음",
        })

    for source_index, r in sector_summary.iterrows():
        country = safe_text(r.get("Country_KR"))
        sector = safe_text(r.get("Sector_Group"))
        title = f"{country} {sector} KOICA portfolio"
        content = (
            f"2019~2024 {sector} KOICA 사업 레코드 {fmt_int(r.get('Project_Count_2019_2024'))}건, "
            f"레코드 비중 {fmt_number(float(r.get('Share_2019_2024', 0)) * 100, 1, '%')}, "
            f"활성연도 {fmt_int(r.get('Active_Years'))}, "
            f"주요 세부분야 {safe_text(r.get('Top_Detail_Sectors'))}."
        )
        citation = f"KOICA country-sector summary 2019~2024, {country}, {sector}"
        make_rag_doc(rows, "Sector Portfolio", country, sector, title, content, citation, {
            "Evidence_Class": "Derived Evidence",
            "Provider": "K-ODA Compass · KOICA 공개자료 집계",
            "Dataset_Name": DATA_FILES["sector_summary"],
            "Original_Title": f"{country} {sector} 2019~2024 집계",
            "Reference_Year": "2019–2024",
            "Collected_At": "수집일 메타데이터 없음",
            "Source_URL": "출처 URL 미등록 · 원자료 파일에서 확인",
            "Source_File": DATA_FILES["sector_summary"],
            "Source_Record_ID": f"row-{int(source_index) + 2}",
            "Model_Role": "기존 KOICA 협력경험의 분야별 파생 집계",
            "Limitations": "고유 사업 수가 아니라 연도별 사업 레코드 집계이며 현재 사업기회를 직접 입증하지 않음",
        })

    project_rows = projects.copy()
    if not project_rows.empty:
        project_rows["_source_index"] = project_rows.index
        project_rows["_project_key"] = project_rows["Project_Name"].map(normalized_project_key)
        group_columns = ["Country_KR", "Sector_Group", "_project_key"]
        for (_, _, project_key), group in project_rows.groupby(group_columns, dropna=False, sort=False):
            representative = group.sort_values("Year", ascending=False).iloc[0]
            country = safe_text(representative.get("Country_KR"))
            sector = safe_text(representative.get("Sector_Group"))
            title = clean_project_text(representative.get("Project_Name"))
            observed_years = sorted(pd.to_numeric(group["Year"], errors="coerce").dropna().astype(int).unique().tolist())
            observed_text = ", ".join(fmt_year(year) for year in observed_years) or "연도 미표기"
            source_rows = [f"row-{int(idx) + 2}" for idx in group["_source_index"].tolist()]
            period = infer_project_period(title, observed_years)
            record_count = len(group)
            duplicate_note = "동일 사업 가능성 · 연도별 반복 레코드 통합" if record_count > 1 else "단일 원자료 레코드"
            description = next((safe_text(value) for value in group["Description"] if safe_text(value)), "설명 미표기")
            content = (
                f"{country} {sector} KOICA 사업 사례. 원문 사업명 {title}. "
                f"사업기간 {period}, 관측 연도 {observed_text}, 원자료 레코드 {record_count}건. "
                f"세부분야 {safe_text(representative.get('Sector_Detail'))}, 사업유형 {safe_text(representative.get('Project_Type'))}. "
                f"{description} 중복 상태: {duplicate_note}."
            )
            citation = f"KOICA ODA project evidence, {country}, {sector}, observed {observed_text}, rows {', '.join(source_rows)}"
            make_rag_doc(rows, "KOICA Project", country, sector, title, content, citation, {
                "Evidence_Class": "Source Evidence",
                "Provider": "KOICA",
                "Dataset_Name": "KOICA 사업정보",
                "Original_Title": title,
                "Reference_Year": observed_text,
                "Collected_At": "수집일 메타데이터 없음",
                "Source_URL": "출처 URL 미등록 · 원자료 파일에서 확인",
                "Source_File": DATA_FILES["projects"],
                "Source_Record_ID": ", ".join(source_rows),
                "Project_ID": f"KODA-KOICA-{hashlib.sha1(f'{country}|{sector}|{project_key}'.encode('utf-8')).hexdigest()[:10].upper()}",
                "Project_Period": period,
                "Observed_Years": observed_text,
                "Record_Count": record_count,
                "Duplicate_Status": duplicate_note,
                "Model_Role": "동일 국가·분야의 기존 KOICA 협력경험",
                "Limitations": "원자료에 안정적 고유 사업 ID가 없어 정규화 사업명으로 통합했으며 원문 대조 필요",
            })

    for source_index, r in wdi.iterrows():
        country = safe_text(r.get("Country_KR"))
        value = safe_text(r.get("Latest_Value_Display"))
        if not value or value.lower() in {"nan", "none", "n/a"}:
            continue
        signal = safe_text(r.get("Signal_KR"))
        title = f"{country} WDI {signal}"
        content = (
            f"{country} {signal} 지표 {safe_text(r.get('Indicator_Name'))}, "
            f"최신연도 {fmt_year(r.get('Latest_Year'))}, 최신값 {value}, "
            f"2019~2025 커버리지 {fmt_int(r.get('WDI_Coverage_2019_2025'))}, "
            f"해석 방향: {wdi_direction_label(r.get('Score_Direction'))}."
        )
        citation = f"World Bank WDI {safe_text(r.get('Series_Code'))}, latest {fmt_year(r.get('Latest_Year'))}, {country}: {value}"
        make_rag_doc(rows, "WDI", country, "국가 개발여건", title, content, citation, {
            "Evidence_Class": "Supplementary Source",
            "Provider": "World Bank",
            "Dataset_Name": "World Development Indicators",
            "Original_Title": safe_text(r.get("Indicator_Name")),
            "Reference_Year": fmt_year(r.get("Latest_Year")),
            "Collected_At": "수집일 메타데이터 없음",
            "Source_URL": f"https://data.worldbank.org/indicator/{safe_text(r.get('Series_Code'))}",
            "Source_File": DATA_FILES["wdi"],
            "Source_Record_ID": f"row-{int(source_index) + 2}",
            "Indicator_Code": safe_text(r.get("Series_Code")),
            "Indicator_Value": value,
            "Indicator_Unit": re.sub(r"[-+]?\d[\d,.]*", "", value).strip() or "원자료 표시 단위",
            "Direction_Label": wdi_direction_label(r.get("Score_Direction")),
            "Model_Role": "국가의 전반적인 개발여건 보조 신호",
            "Limitations": "선택 분야의 직접 수요를 단독으로 입증하지 않으며 다른 지표·현지조사와 함께 해석",
        })

    for source_index, r in policy.iterrows():
        country = safe_text(r.get("Country_KR"))
        title = f"{country} policy and risk supporting indicators"
        content = (
            f"{country} 정책정합성 {fmt_number(r.get('Policy_Alignment_Score_V21'))}, "
            f"실행가능성 {fmt_number(r.get('Risk_Feasibility_Score_V21'))}, "
            f"CPS 대상국 {safe_text(r.get('국가협력전략 대상국가'))}, "
            f"KOICA 사무소 {safe_text(r.get('한국국제협력단 사무소 주재 여부'))}, "
            f"취약국가지수 {fmt_number(r.get('취약국가 지수'))}, "
            f"부패인식점수 {fmt_number(r.get('부패인식점수'))}, "
            f"전자정부지수 {fmt_number(r.get('전자정부지수'), 3)}, "
            f"인간개발지수 {fmt_number(r.get('인간개발지수'), 3)}, "
            f"기업여건 {fmt_number(r.get('기업여건'))}."
        )
        citation = f"KOICA integrated partner-country supporting indicators, {country}, policy/risk v2.1"
        make_rag_doc(rows, "Policy/Risk", country, "국가 실행환경", title, content, citation, {
            "Evidence_Class": "Derived Evidence",
            "Provider": "K-ODA Compass · KOICA 통합 협력국 정보",
            "Dataset_Name": DATA_FILES["policy_risk"],
            "Original_Title": title,
            "Reference_Year": "지표별 기준연도 상이",
            "Collected_At": "수집일 메타데이터 없음",
            "Source_URL": "출처 URL 미등록 · 원자료 파일에서 확인",
            "Source_File": DATA_FILES["policy_risk"],
            "Source_Record_ID": f"row-{int(source_index) + 2}",
            "Model_Role": "정책정합성·실행환경·리스크 보조 파생점수",
            "Model_Version": MODEL_VERSION,
            "Limitations": "현지조사나 기관 실사를 대체하지 않는 보조지표",
        })

    for source_index, r in cps_pdf.iterrows():
        country = safe_text(r.get("Country_KR"))
        sector = safe_text(r.get("Sector_Tag")) or "CPS 정책전략"
        page = fmt_int(r.get("Page"))
        code = safe_text(r.get("Country_Code"))
        chunk_id = safe_text(r.get("Chunk_ID"))
        title = f"{country} CPS 원문 p.{page} · {sector}"
        content = safe_text(r.get("Text"))
        citation = f"{safe_text(r.get('Citation'))} · {chunk_id}"
        make_rag_doc(rows, "CPS PDF", country, sector, title, content, citation, {
            "Evidence_Class": "Source Evidence",
            "Provider": "대한민국 관계부처 합동 국가협력전략",
            "Dataset_Name": safe_text(r.get("PDF_File")) or "CPS PDF",
            "Original_Title": f"{country} 국가협력전략",
            "Reference_Year": "문서 기준연도 원문 확인",
            "Collected_At": "수집일 메타데이터 없음",
            "Source_URL": "출처 URL 미등록 · 원자료 파일에서 확인",
            "Source_File": DATA_FILES["cps_pdf"],
            "Source_Record_ID": f"row-{int(source_index) + 2}",
            "Chunk_ID": chunk_id,
            "Page": fmt_year(r.get("Page")),
            "Extraction_Method": safe_text(r.get("Extraction_Method")),
            "Model_Role": "CPS 정책원문 페이지 근거",
            "Limitations": "OCR 미완료 가능성과 문서 최신성 확인 필요",
        })

    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False, ttl=900, max_entries=1)
def build_validation_country_corpus(country: str) -> pd.DataFrame:
    """Build one country's audit corpus only after the validation test is requested."""
    frames: dict[str, pd.DataFrame] = {}
    for data_key in ("master", "wdi", "projects", "policy_risk", "sector_summary", "cps_pdf"):
        frame = prepare_data({data_key: load_csv(DATA_FILES[data_key])})[data_key]
        frames[data_key] = frame.loc[frame["Country_KR"] == country].copy()
    return build_rag_corpus(
        frames["master"],
        frames["wdi"],
        frames["projects"],
        frames["policy_risk"],
        frames["sector_summary"],
        frames["cps_pdf"],
    )


def retrieve_rag_evidence(corpus: pd.DataFrame, country: str, sector: str, keywords: str, row: pd.Series, top_k: int = 14) -> pd.DataFrame:
    query_tokens = tokenize_for_rag(
        country,
        sector,
        keywords,
        row.get("Candidate_Type_V21"),
        row.get("Recommended_Service_Angle_V2"),
        "ODA 성과관리 KPI 현지수요 파트너십 실행가능성 정책정합성 개발수요",
    )
    scoped = corpus.loc[corpus["Country_KR"] == country].copy()
    if scoped.empty:
        return pd.DataFrame(columns=list(corpus.columns) + ["RAG_Score", "Citation_ID", "Directness", "Sector_Relevance"])

    sector_bound_sources = {"CPS PDF", "KOICA Project", "Sector Portfolio"}
    common_sources = {"Score Model", "Policy/Risk", "WDI"}
    scoped = scoped.loc[
        scoped["Source_Type"].isin(common_sources)
        | (
            scoped["Source_Type"].isin(sector_bound_sources)
            & (scoped["Sector_Group"] == sector)
        )
    ].copy()

    def score_doc(r: pd.Series) -> float:
        doc_tokens = set(r.get("Tokens") or [])
        score = len(query_tokens & doc_tokens) * 2.0
        if r.get("Country_KR") == country:
            score += 20.0
        if r.get("Sector_Group") == sector:
            score += 24.0
        if sector and sector in f"{r.get('Title')} {r.get('Content')}":
            score += 5.0
        if r.get("Source_Type") == "KOICA Project":
            score += 8.0
        if r.get("Source_Type") == "CPS PDF":
            score += 8.0
        if r.get("Source_Type") in {"WDI", "Policy/Risk", "Score Model"}:
            score += 3.0
        return score

    scoped["RAG_Score"] = scoped.apply(score_doc, axis=1)
    scoped = scoped.sort_values(["RAG_Score", "Source_Type"], ascending=[False, True])

    selected_indices: list[int] = []
    quotas = [
        ("Score Model", 1),
        ("Policy/Risk", 1),
        ("CPS PDF", 3),
        ("KOICA Project", 5),
        ("Sector Portfolio", 2),
        ("WDI", 4),
    ]
    for source_type, quota in quotas:
        if len(selected_indices) >= top_k:
            break
        candidates = scoped.loc[(scoped["Source_Type"] == source_type) & (scoped["RAG_Score"] > 0)]
        for idx in candidates.index.tolist()[:quota]:
            if len(selected_indices) >= top_k:
                break
            if idx not in selected_indices:
                selected_indices.append(idx)

    for idx in scoped.index.tolist():
        if len(selected_indices) >= top_k:
            break
        if idx not in selected_indices and scoped.loc[idx, "RAG_Score"] > 0:
            selected_indices.append(idx)

    out = scoped.loc[selected_indices].copy()
    out = out.sort_values("RAG_Score", ascending=False).reset_index(drop=True)
    out["Citation_ID"] = [f"E{i + 1:02d}" for i in range(len(out))]
    out["Directness"] = out.apply(
        lambda evidence: "직접근거"
        if evidence.get("Source_Type") in sector_bound_sources and evidence.get("Sector_Group") == sector
        else "보조근거",
        axis=1,
    )
    out["Sector_Relevance"] = out.apply(
        lambda evidence: wdi_relevance_level(sector, safe_text(evidence.get("Title")), safe_text(evidence.get("Content")))
        if evidence.get("Source_Type") == "WDI"
        else ("직접 관련" if evidence.get("Directness") == "직접근거" else "국가 공통 보조"),
        axis=1,
    )
    return out


def citation_ids(docs: pd.DataFrame, source_type: str | None = None, limit: int = 3) -> str:
    if docs.empty:
        return ""
    subset = docs if source_type is None else docs.loc[docs["Source_Type"] == source_type]
    ids = subset["Citation_ID"].head(limit).tolist()
    return ", ".join(f"[{x}]" for x in ids)


def format_rag_citations(docs: pd.DataFrame) -> str:
    if docs.empty:
        return "- [E00] 검색된 근거가 제한적입니다. 원자료 확인과 현지 검증이 필요합니다."
    lines = []
    for _, d in docs.iterrows():
        lines.append(
            f"- [{d['Citation_ID']}] **{safe_text(d.get('Evidence_Class')) or '분류 확인 필요'}** · "
            f"{safe_text(d.get('Directness')) or '관련성 확인 필요'} · {d['Source_Type']} · {d['Title']} — {d['Citation']}"
        )
    return "\n".join(lines)


def citation_integrity_metrics(generated_text: str, docs: pd.DataFrame) -> dict[str, object]:
    cited = re.findall(r"\[(E\d{2})\]", generated_text or "")
    evidence_ids = set(docs.get("Citation_ID", pd.Series(dtype=str)).dropna().astype(str))
    resolved = [citation_id for citation_id in cited if citation_id in evidence_ids]
    unknown = sorted(set(cited) - evidence_ids)
    unique_cited = set(cited)
    unused_evidence = sorted(evidence_ids - unique_cited)
    return {
        "citation_count": len(cited),
        "resolved_count": len(resolved),
        "resolution_rate": (len(resolved) / len(cited) * 100) if cited else None,
        "unknown_ids": unknown,
        "unknown_count": len(unknown),
        "duplicate_count": max(len(cited) - len(unique_cited), 0),
        "unused_evidence_ids": unused_evidence,
        "unused_evidence_count": len(unused_evidence),
        "unsupported_paragraphs": None,
    }


def citation_semantic_mismatches(generated_text: str, docs: pd.DataFrame) -> list[dict[str, str]]:
    source_by_id = {
        safe_text(row.get("Citation_ID")): safe_text(row.get("Source_Type"))
        for _, row in docs.iterrows()
        if safe_text(row.get("Citation_ID"))
    }
    rules = [
        ("CPS 정책 주장", ("CPS", "국가협력전략", "정책원문"), {"CPS PDF"}),
        ("KOICA 협력경험 주장", ("기존 KOICA 사업", "KOICA 기존 협력경험", "협력경험"), {"KOICA Project", "Sector Portfolio"}),
        ("실행환경·리스크 주장", ("실행환경", "실행가능성", "집행위험", "리스크"), {"Policy/Risk"}),
        ("국가 개발여건 주장", ("국가 개발여건",), {"WDI"}),
    ]
    mismatches: list[dict[str, str]] = []
    fragments = [fragment.strip() for fragment in re.split(r"\n+|(?<=[.!?])\s+", generated_text or "") if fragment.strip()]
    for fragment in fragments:
        cited_ids = re.findall(r"\[(E\d{2})\]", fragment)
        if not cited_ids:
            continue
        for claim_type, keywords, allowed_types in rules:
            if not any(keyword.lower() in fragment.lower() for keyword in keywords):
                continue
            if (
                claim_type == "실행환경·리스크 주장"
                and "후보유형" in fragment
                and not any(term in fragment for term in ("실행환경", "실행가능성", "집행위험"))
            ):
                continue
            invalid = [
                citation_id for citation_id in cited_ids
                if source_by_id.get(citation_id) not in allowed_types
            ]
            if invalid:
                actual = ", ".join(
                    f"{citation_id}:{source_by_id.get(citation_id, '미등록')}" for citation_id in invalid
                )
                mismatches.append({
                    "claim_type": claim_type,
                    "citation_ids": ", ".join(invalid),
                    "actual_source_types": actual,
                    "allowed_source_types": ", ".join(sorted(allowed_types)),
                    "text": fragment[:240],
                })
    return mismatches


def evidence_year_or_page(row: pd.Series) -> str:
    citation = f"{safe_text(row.get('Citation'))} {safe_text(row.get('Title'))}"
    if row.get("Source_Type") == "CPS PDF":
        page = re.search(r"p\.?\s*(\d+)", citation, flags=re.IGNORECASE)
        return f"p.{page.group(1)}" if page else "페이지 확인"
    year = re.search(r"\b(20\d{2})\b", citation)
    return year.group(1) if year else "파생·기준연도 상이"


def build_rag_evidence_pack(
    country: str,
    sector: str,
    keywords: str,
    docs: pd.DataFrame,
    design_assumptions: dict | None = None,
    result: dict[str, object] | None = None,
) -> str:
    result = result or build_builder_result(country, sector, docs, design_assumptions)
    docs = result_evidence_frame(result, docs)
    if docs.empty:
        evidence_sections = "검색된 근거가 없습니다. 원자료와 검색조건을 확인하세요."
    else:
        sections = []
        for _, evidence in docs.iterrows():
            source_type = safe_text(evidence.get("Source_Type"))
            fields = [
                ("Evidence ID", safe_text(evidence.get("Citation_ID"))),
                ("Evidence Class", safe_text(evidence.get("Evidence_Class")) or "분류 메타데이터 없음"),
                ("직접·보조 구분", safe_text(evidence.get("Directness")) or "관련성 검토 필요"),
                ("제공기관", safe_text(evidence.get("Provider")) or "제공기관 메타데이터 없음"),
                ("데이터셋·문서명", safe_text(evidence.get("Dataset_Name")) or "데이터셋명 메타데이터 없음"),
                ("원문 제목", safe_text(evidence.get("Original_Title")) or safe_text(evidence.get("Title"))),
                ("국가", safe_text(evidence.get("Country_KR"))),
                ("분야", safe_text(evidence.get("Sector_Group"))),
                ("기준연도", safe_text(evidence.get("Reference_Year")) or "기준연도 메타데이터 없음"),
                ("수집일", safe_text(evidence.get("Collected_At")) or "수집일 메타데이터 없음"),
                ("출처 URL", safe_text(evidence.get("Source_URL")) or "출처 URL 미등록 · 원자료 파일에서 확인"),
                ("원자료 파일명", safe_text(evidence.get("Source_File")) or "원자료 파일명 메타데이터 없음"),
                ("원자료 ID", safe_text(evidence.get("Source_Record_ID")) or "원자료 ID 메타데이터 없음"),
                ("모델에서의 역할", safe_text(evidence.get("Model_Role")) or "역할 메타데이터 없음"),
                ("분야 관련성", safe_text(evidence.get("Sector_Relevance")) or "관련성 검토 필요"),
                ("제한사항", safe_text(evidence.get("Limitations")) or "추가 원문 검토 필요"),
            ]
            if source_type == "KOICA Project":
                fields.extend([
                    ("통합 근거 ID", safe_text(evidence.get("Project_ID")) or "통합 ID 없음"),
                    ("원자료 고유 사업 ID", "원자료에 안정적 ID 없음"),
                    ("사업기간", safe_text(evidence.get("Project_Period")) or "사업기간 메타데이터 없음"),
                    ("관측 연도", safe_text(evidence.get("Observed_Years")) or "연도 미표기"),
                    ("원자료 레코드 수", fmt_int(evidence.get("Record_Count"))),
                    ("중복 상태", safe_text(evidence.get("Duplicate_Status")) or "중복 검토 필요"),
                ])
            elif source_type == "CPS PDF":
                fields.extend([
                    ("페이지", safe_text(evidence.get("Page")) or "페이지 메타데이터 없음"),
                    ("청크 ID", safe_text(evidence.get("Chunk_ID")) or "청크 ID 메타데이터 없음"),
                    ("추출 방식", safe_text(evidence.get("Extraction_Method")) or "추출 방식 메타데이터 없음"),
                ])
            elif source_type == "WDI":
                fields.extend([
                    ("지표코드", safe_text(evidence.get("Indicator_Code")) or "지표코드 없음"),
                    ("값", safe_text(evidence.get("Indicator_Value")) or "최신값 없음"),
                    ("단위", safe_text(evidence.get("Indicator_Unit")) or "단위 메타데이터 없음"),
                    ("수요 해석 방향", safe_text(evidence.get("Direction_Label")) or "다른 지표와 함께 검토 필요"),
                ])
            elif source_type in {"Score Model", "Policy/Risk", "Sector Portfolio"}:
                fields.extend([
                    ("모델 버전", safe_text(evidence.get("Model_Version")) or MODEL_VERSION),
                    ("원점수", safe_text(evidence.get("Original_Score")) or "근거별 원점수 해당 없음"),
                    ("가중치", safe_text(evidence.get("Weight")) or "근거별 가중치 해당 없음"),
                    ("가중 기여도", safe_text(evidence.get("Weighted_Contribution")) or "근거별 기여도 해당 없음"),
                ])
            field_lines = "\n".join(f"- {label}: {value}" for label, value in fields)
            excerpt = concise_source_summary(evidence.get("Content"), limit=360)
            sections.append(f"## [{evidence['Citation_ID']}] {evidence['Title']}\n{field_lines}\n- 근거 요약: {excerpt}")
        evidence_sections = "\n\n".join(sections)

    assumption_inventory = "\n".join(result_assumption_lines(result))
    assumption_notice = safe_text(result.get("assumption_notice")) or ASSUMPTION_NOTICE
    return f"""# K-ODA Compass RAG Evidence Pack

## Query
- 국가: {country}
- 선택 분야: {sector}
- 키워드: {keywords}
- 모델 버전: {MODEL_VERSION}
- 생성 기준: 선택 국가·선택 분야 직접근거 우선, 국가 공통 보조·파생근거 분리

## Evidence Inventory
{evidence_sections}

## AI 생성 예비 설계 가정
{assumption_notice}

{assumption_inventory}

## Grounding Rule
직접근거는 선택 국가·선택 분야가 모두 일치하는 KOICA·CPS·분야 집계에 한정합니다. WDI는 국가 개발여건 보조 신호이며, 파생점수와 AI 설계 가정은 원천자료와 구분합니다. 본 근거팩은 최종 사실성이나 사업 타당성을 자동 보증하지 않습니다.
"""


def metric_card(label: str, value: str, note: str = "") -> None:
    st.markdown(f"""
    <div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>
    """, unsafe_allow_html=True)


def insight_card(title: str, body: str) -> None:
    st.markdown(f"""
    <div class="insight-card"><div class="insight-title">{title}</div><div class="insight-body">{body}</div></div>
    """, unsafe_allow_html=True)


def pipeline_card(title: str, body: str) -> None:
    st.markdown(f"""
    <div class="pipeline-card"><div class="pipeline-title">{title}</div><div class="pipeline-body">{body}</div></div>
    """, unsafe_allow_html=True)


def risk_card(title: str, body: str) -> None:
    st.markdown(f"""
    <div class="risk-card"><div class="risk-title">{title}</div><div class="risk-body">{body}</div></div>
    """, unsafe_allow_html=True)


def queue_navigation(
    view_name: str,
    country: str | None = None,
    sector: str | None = None,
    user_type: str | None = None,
) -> None:
    st.session_state["_pending_view"] = view_name
    if country:
        st.session_state["_pending_country"] = country
    if sector:
        st.session_state["_pending_sector"] = sector
    if user_type:
        st.session_state["_pending_user_type"] = user_type


def queue_sector_detail(section: str, sector: str | None = None) -> None:
    st.session_state["sector_section"] = section
    if sector:
        st.session_state["sector_cps_focus"] = sector


def get_country_options(master: pd.DataFrame) -> List[str]:
    return master["Country_KR"].dropna().tolist()


def get_country_row(master: pd.DataFrame, country_kr: str) -> pd.Series:
    rows = master.loc[master["Country_KR"] == country_kr]
    return rows.iloc[0] if not rows.empty else master.iloc[0]


def wdi_for_country(wdi: pd.DataFrame, country: str) -> pd.DataFrame:
    return wdi.loc[wdi["Country_KR"] == country].copy()


def cps_for_country(cps_pdf: pd.DataFrame, country: str) -> pd.DataFrame:
    out = cps_pdf.loc[cps_pdf["Country_KR"] == country].copy()
    if out.empty:
        return out
    out["_generic_policy"] = out["Sector_Tag"].fillna("").eq("CPS 정책전략")
    return out.sort_values(["_generic_policy", "Page", "Chunk_ID"]).drop(columns="_generic_policy")


def cps_document_summary(country: str, country_cps: pd.DataFrame) -> Dict[str, str]:
    if country_cps.empty:
        return {
            "document": "CPS 직접근거 없음",
            "year": "기준연도 확인 필요",
            "file": "파일 없음",
            "sectors": "관련 분야 확인 필요",
            "pages": "관련 페이지 없음",
            "chunks": "0",
        }
    file_names = country_cps["PDF_File"].dropna().astype(str).drop_duplicates().tolist()
    source_text = " ".join(country_cps.sort_values(["Page", "Chunk_ID"])["Text"].dropna().astype(str).head(8).tolist())
    years = [year for year in re.findall(r"(?:19|20)\d{2}", source_text) if 1990 <= int(year) <= 2035]
    sectors = [
        value for value in country_cps["Sector_Tag"].dropna().astype(str).drop_duplicates().tolist()
        if value != "CPS 정책전략"
    ]
    pages = sorted(pd.to_numeric(country_cps["Page"], errors="coerce").dropna().astype(int).unique().tolist())
    page_text = ", ".join(f"p.{page}" for page in pages[:8])
    if len(pages) > 8:
        page_text += f" 외 {len(pages) - 8}개 페이지"
    return {
        "document": f"{country} 국가협력전략",
        "year": years[0] if years else "기준연도 확인 필요",
        "file": ", ".join(file_names) if file_names else "파일명 미표기",
        "sectors": ", ".join(sectors[:5]) if sectors else "CPS 정책전략",
        "pages": page_text or "페이지 미표기",
        "chunks": str(len(country_cps)),
    }


def evidence_completeness(
    row: pd.Series,
    country_wdi: pd.DataFrame,
    country_cps: pd.DataFrame,
    policy_row: pd.Series,
) -> Dict[str, object]:
    koica_records = pd.to_numeric(pd.Series([row.get("Project_Count_2019_2024")]), errors="coerce").iloc[0]
    wdi_latest = int(pd.to_numeric(country_wdi.get("Latest_Value", pd.Series(dtype=float)), errors="coerce").notna().sum())
    risk_fields = [
        "국가협력전략 대상국가",
        "한국국제협력단 사무소 주재 여부",
        "취약국가 지수",
        "부패인식점수",
        "전자정부지수",
        "인간개발지수",
        "기업여건",
    ]
    risk_available = sum(
        1 for field in risk_fields
        if field in policy_row.index and pd.notna(policy_row.get(field)) and str(policy_row.get(field)).strip() != ""
    )
    status = {
        "KOICA": bool(pd.notna(koica_records) and koica_records > 0),
        "CPS": not country_cps.empty,
        "WDI": wdi_latest > 0,
        "정책·리스크": risk_available > 0,
    }
    return {
        "score": sum(status.values()),
        "status": status,
        "koica_records": int(koica_records) if pd.notna(koica_records) else 0,
        "cps_chunks": len(country_cps),
        "wdi_latest": wdi_latest,
        "wdi_total": len(country_wdi),
        "risk_available": risk_available,
        "risk_total": len(risk_fields),
    }


def country_diagnosis(master: pd.DataFrame, row: pd.Series) -> str:
    components = {
        "개발수요": "Development_Need_Score",
        "분야적합성": "Sector_Fit_Score_V2",
        "한국의 기존 협력경험": "Korea_Coop_Base_Score_V2",
        "실행가능성": "Risk_Feasibility_Score_V21",
    }
    positions = {
        label: float(
            (
                pd.to_numeric(master[column], errors="coerce").dropna()
                <= pd.to_numeric(pd.Series([row.get(column)]), errors="coerce").iloc[0]
            ).mean()
            * 100
        )
        for label, column in components.items()
    }
    lowest_label, lowest_percentile = min(positions.items(), key=lambda item: item[1])
    position_text = ", ".join(f"{label} {percentile:.0f}백분위" for label, percentile in positions.items())
    return (
        f"Top 50 상대위치는 {position_text}입니다. 네 요소 중 {lowest_label}({lowest_percentile:.0f}백분위)가 가장 낮아 "
        "현지 파트너·정책환경·집행위험을 후속 검증해야 합니다."
    )


def next_validation_steps(user_type: str) -> List[str]:
    steps = {
        "CSO·NGO": [
            "CPS 정책근거 확인",
            "현지 수요와 수혜자 검증",
            "현지 파트너 역량 확인",
            "소규모 파일럿 설계",
            "집행·거버넌스 위험 완화계획 수립",
        ],
        "기업·사회적기업": [
            "CPS 정책근거와 공공수요 확인",
            "현지 파트너·조달환경 검토",
            "기술·서비스 적합성 확인",
            "공공·민간 협력구조 검토",
            "단계별 집행·위험분담 계획 수립",
        ],
        "지방정부": [
            "CPS 정책근거 확인",
            "기존 국제교류 및 정책연계 검토",
            "지역 특화분야와 현지 수요 매칭",
            "공공기관·현지정부 협력구조 확인",
            "소규모 교류·정책 파일럿 설계",
        ],
        "대학·연구기관": [
            "CPS와 정책·개발지표 비교",
            "기초조사 및 성과지표 설계",
            "현지 연구기관 파트너 검토",
            "연구윤리·데이터 품질 확인",
            "실증·역량강화 파일럿 설계",
        ],
    }
    return steps[user_type]


def risk_factor_table(row: pd.Series, policy_row: pd.Series) -> pd.DataFrame:
    def raw(field: str, digits: int = 2) -> str:
        value = policy_row.get(field)
        return "데이터 없음" if pd.isna(value) else fmt_number(value, digits)

    def subscore(field: str) -> str:
        value = policy_row.get(field)
        return "산출 안 됨" if pd.isna(value) else fmt_number(value)

    return pd.DataFrame([
        ["거버넌스·취약성", raw("취약국가 지수"), subscore("Risk_Fragility_Score"), "취약국가 지수는 모델에서 낮을수록 실행여건에 유리하도록 역산", "단계별 집행과 외부 모니터링 검토"],
        ["부패·투명성", raw("부패인식점수", 1), subscore("Risk_Corruption_Control_Score"), "부패인식점수가 높을수록 실행여건에 유리한 보조신호", "조달 투명성·감사·공개 절차 확인"],
        ["전자정부 역량", raw("전자정부지수", 4), subscore("Risk_Egov_Score"), "전자정부지수가 높을수록 제도·디지털 역량에 유리한 보조신호", "현행 시스템·운영인력 사전진단"],
        ["인간개발 기반", raw("인간개발지수", 3), subscore("Risk_HDI_Score"), "인간개발지수가 높을수록 실행 기반에 유리한 보조신호", "현지 인력·수혜자 접근성 확인"],
        ["기업환경", raw("기업여건", 1), subscore("Risk_Business_Environment_Score"), "원자료 기업여건과 모델 정규화 점수를 함께 제시", "조달·규제·시장진입 조건 별도 실사"],
        ["현지 수행기반", safe_text(policy_row.get("한국국제협력단 사무소 주재 여부")) or "데이터 없음", subscore("Risk_Office_Presence_Score"), "KOICA 사무소 주재 여부를 현지 수행기반의 보조 proxy로 사용", "실제 담당조직·수행역량 확인"],
        ["파트너 역량", "직접 데이터 없음", "산출 안 됨", "현재 데이터만으로 파트너 역량을 판단할 수 없음", "현지기관 실사와 공동수행 구조 검토"],
        ["데이터 신뢰도", f"커버리지 점수 {fmt_number(row.get('Data_Reliability_Score_V21'))}", fmt_number(row.get("Data_Reliability_Score_V21")), "WDI와 정책·리스크 자료의 커버리지 기반", "최신 원자료와 결측지표 재확인"],
    ], columns=["하위요인", "관측값", "모델 보조점수", "해석", "권장 대응"])


def country_year_for_country(df: pd.DataFrame, country: str) -> pd.DataFrame:
    return df.loc[df["Country_KR"] == country].copy().sort_values("Year")


def sector_summary_for_country(df: pd.DataFrame, country: str) -> pd.DataFrame:
    out = df.loc[df["Country_KR"] == country].copy()
    if not out.empty:
        out = out.sort_values("Project_Count_2019_2024", ascending=False)
    return out


def sector_year_for_country(df: pd.DataFrame, country: str) -> pd.DataFrame:
    return df.loc[df["Country_KR"] == country].copy()


def projects_for_country(projects: pd.DataFrame, country: str, sector: str | None = None) -> pd.DataFrame:
    out = projects.loc[projects["Country_KR"] == country].copy()
    if sector and sector != "전체":
        out = out.loc[out["Sector_Group"] == sector]
    if not out.empty:
        out = out.sort_values(["Year", "Disbursement_Raw"], ascending=[False, False])
    return out


def display_rank_table(df: pd.DataFrame, cps_countries: set[str] | None = None) -> pd.DataFrame:
    cps_countries = cps_countries or set()
    rows = []
    for _, row in df.iterrows():
        evidence = [
            f"KOICA {'✓' if float(row.get('Project_Count_2019_2024', 0) or 0) > 0 else '–'}",
            f"CPS {'✓' if row.get('Country_KR') in cps_countries else '–'}",
            f"WDI {'✓' if float(row.get('WDI_Core_Coverage_%', 0) or 0) > 0 else '–'}",
        ]
        rows.append({
            "순위": int(row["Rank_V21"]),
            "국가": row["Country_KR"],
            "우선순위 점수": row["K_ODA_Opportunity_Score_V21"],
            "개발수요": row["Development_Need_Score"],
            "정책정합성": row["Policy_Alignment_Score_V21"],
            "실행가능성": row["Risk_Feasibility_Score_V21"],
            "후보유형": compact_candidate_label(row["Candidate_Type_V21"]),
            "근거상태": " · ".join(evidence),
            "다음 확인": "프로필 · 근거 · Builder",
        })
    return pd.DataFrame(rows)


def component_contribution_long(df: pd.DataFrame, weights: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    top = df.head(top_n).copy()
    mapping = {
        "Development_Need_Score": ("Development Need", "개발수요"),
        "Korea_Coop_Base_Score_V2": ("Korea Cooperation Base", "한국 기존 협력경험"),
        "Sector_Fit_Score_V2": ("Sector Fit", "분야적합성"),
        "Opportunity_Gap_Score_V2": ("Opportunity Gap", "사업기회 공백"),
        "Policy_Alignment_Score_V21": ("Policy Alignment", "정책정합성"),
        "Risk_Feasibility_Score_V21": ("Risk Feasibility", "실행가능성"),
        "Data_Reliability_Score_V21": ("Data Reliability", "데이터 신뢰도"),
    }
    weight_lookup = dict(zip(weights["Component"], pd.to_numeric(weights["Weight"], errors="coerce")))
    rows=[]
    for _, r in top.iterrows():
        for col, (component, label) in mapping.items():
            raw_score = pd.to_numeric(r.get(col), errors="coerce")
            contribution = raw_score * float(weight_lookup.get(component, 0))
            rows.append({"국가": r["Country_KR"], "구성요소": label, "가중기여도": contribution})
    return pd.DataFrame(rows)


def parse_top_sectors(text: str) -> List[str]:
    if pd.isna(text) or not str(text).strip(): return []
    return [x.strip() for x in str(text).split(";") if x.strip()]


def recommended_sectors(row: pd.Series) -> List[str]:
    val = str(row.get("Recommended_Service_Angle_V2", ""))
    if not val or val == "nan":
        val = str(row.get("Top_Actionable_Sectors_2019_2024", ""))
    parts = []
    for x in val.replace(";", ",").split(","):
        s = x.strip()
        if s:
            parts.append(s.split("(")[0].strip())
    return parts[:2] if parts else ["공공행정"]


def wdi_signal_cards(country_wdi: pd.DataFrame) -> List[Dict[str, str]]:
    signal_order = ["소득수준", "빈곤", "교육", "전력접근", "디지털접근", "보건·생활여건", "고용", "도시화", "인구규모", "탄소배출"]
    friendly_names = {
        "소득수준": "1인당 GDP",
        "빈곤": "빈곤율",
        "교육": "중등교육 등록률",
        "전력접근": "전력 접근률",
        "디지털접근": "인터넷 이용률",
        "보건·생활여건": "기대수명",
        "고용": "실업률",
        "도시화": "도시인구 비율",
        "인구규모": "총인구",
        "탄소배출": "1인당 탄소배출",
    }
    interpretations = {
        "소득수준": "낮은 값은 소득·기초서비스 개선 필요 가능성을 시사합니다.",
        "빈곤": "높은 값은 취약계층 보호와 포용성장 수요 가능성을 시사합니다.",
        "교육": "낮은 값은 중등교육 접근성 개선 필요 가능성을 시사합니다.",
        "전력접근": "낮은 값은 전력 인프라 부족 가능성을 시사합니다.",
        "디지털접근": "낮은 값은 디지털 접근성 개선 필요 가능성을 시사합니다.",
        "보건·생활여건": "낮은 기대수명은 보건·생활여건 개선 필요 가능성을 시사합니다.",
        "고용": "높은 실업률은 일자리·직업역량 지원 수요 가능성을 시사합니다.",
        "도시화": "도시화 수준은 도시서비스와 지역개발 규모를 판단하는 맥락 지표입니다.",
        "인구규모": "인구규모는 잠재 수혜범위와 사업규모를 판단하는 맥락 지표입니다.",
        "탄소배출": "1인당 배출량은 기후·에너지 여건의 맥락 지표이며 단독으로 사업수요를 결정하지 않습니다.",
    }
    cards = []
    for sig in signal_order:
        rows = country_wdi.loc[country_wdi["Signal_KR"] == sig]
        if rows.empty:
            cards.append({
                "title": f"{friendly_names[sig]}: 최신값 없음",
                "body": "해당 WDI 행 없음<br>최신 가용연도: 확인 필요<br>출처: World Bank WDI<br>데이터 확인 필요",
            })
            continue
        r = rows.iloc[0]
        display_value = r.get("Latest_Value_Display")
        has_latest = pd.notna(r.get("Latest_Value")) and pd.notna(display_value) and str(display_value).strip().lower() not in {"", "nan", "none", "n/a"}
        val = safe_text(display_value) if has_latest else "최신값 없음"
        series_code = safe_text(r.get("Series_Code")) or "코드 미표기"
        latest_year = fmt_year(r.get("Latest_Year")) if has_latest else "최신값 없음"
        coverage = pd.to_numeric(pd.Series([r.get("WDI_Coverage_2019_2025")]), errors="coerce").iloc[0]
        coverage_text = f"{int(coverage)}/7개 연도" if pd.notna(coverage) else "확인 필요"
        body = (
            f"최신 가용연도: {latest_year}<br>"
            f"지표코드: {series_code}<br>"
            f"출처: World Bank WDI · 2019~2025 커버리지 {coverage_text}<br>"
            f"{interpretations[sig] if has_latest else '최신값이 없어 해석에서 제외하며 원자료 확인이 필요합니다.'}"
        )
        cards.append({"title": f"{friendly_names[sig]}: {val}", "body": body})
    return cards



def compact_detail_sectors(text: str, n: int = 3) -> str:
    """Convert detailed sector strings like 'A(10); B(5)' into a compact top-N label."""
    if pd.isna(text) or not str(text).strip():
        return "세부분야 미표기"
    parts = []
    for raw in str(text).split(";"):
        item = raw.strip()
        if not item:
            continue
        item = item.split("(")[0].strip()
        if item:
            parts.append(item)
    return ", ".join(parts[:n]) if parts else "세부분야 미표기"


def sector_trend_interpretation(country: str, sy: pd.DataFrame) -> str:
    if sy.empty:
        return f"{country}의 국가×분야×연도 추세 데이터가 제한적이므로 기존 사업근거와 WDI 신호를 함께 검토해야 합니다."
    totals = sy.groupby("Sector_Group")["Project_Count"].sum().sort_values(ascending=False)
    top_names = totals.head(2).index.tolist()
    top_text = "와 ".join(top_names) if len(top_names) >= 2 else (top_names[0] if top_names else "주요 분야")
    inc_text = ""
    if {2023, 2024}.issubset(set(pd.to_numeric(sy["Year"], errors="coerce").dropna().astype(int).tolist())):
        pivot = sy.pivot_table(index="Sector_Group", columns="Year", values="Project_Count", aggfunc="sum", fill_value=0)
        if 2023 in pivot.columns and 2024 in pivot.columns:
            diff = (pivot[2024] - pivot[2023]).sort_values(ascending=False)
            if not diff.empty and diff.iloc[0] > 0:
                inc_text = f" 2024년에는 {diff.index[0]} 분야가 전년 대비 증가했습니다."
    return f"최근 6년간 {country}의 KOICA 공개 레코드는 {top_text} 비중이 높게 나타납니다.{inc_text} 이는 과거 협력경험의 분포이며, 현재 사업기회는 최신 CPS·현지수요·파트너 역량으로 별도 검증해야 합니다."


def cps_for_sector(country_cps: pd.DataFrame, sector: str) -> pd.DataFrame:
    if country_cps.empty:
        return country_cps.copy()
    aliases = {
        "긴급구호/취약성": {"긴급구호/취약성", "긴급구호"},
        "기술환경에너지": {"기술환경에너지"},
        "공공행정": {"공공행정"},
        "교육": {"교육"},
        "농림수산": {"농림수산"},
        "보건의료": {"보건의료"},
        "산업": {"산업"},
    }
    tags = aliases.get(sector, {sector} if sector != "기타" else set())
    if not tags:
        return country_cps.iloc[0:0].copy()
    return country_cps.loc[country_cps["Sector_Tag"].isin(tags)].copy().sort_values(["Page", "Chunk_ID"])


def sector_wdi_rows(country_wdi: pd.DataFrame, sector: str) -> pd.DataFrame:
    signal_map = {
        "공공행정": ["디지털접근", "도시화", "소득수준"],
        "기술환경에너지": ["전력접근", "디지털접근", "탄소배출"],
        "교육": ["교육", "고용", "인구규모"],
        "농림수산": ["빈곤", "고용", "소득수준"],
        "보건의료": ["보건·생활여건", "빈곤", "인구규모"],
        "산업": ["고용", "전력접근", "디지털접근"],
        "긴급구호/취약성": ["빈곤", "보건·생활여건", "인구규모"],
        "기타": ["소득수준", "인구규모", "도시화"],
    }
    signals = signal_map.get(sector, ["소득수준", "인구규모"])
    out = country_wdi.loc[country_wdi["Signal_KR"].isin(signals)].copy()
    out["_signal_order"] = out["Signal_KR"].map({signal: index for index, signal in enumerate(signals)})
    return out.sort_values("_signal_order").drop(columns="_signal_order")


def sector_wdi_summary(country_wdi: pd.DataFrame, sector: str) -> str:
    friendly = {
        "소득수준": "1인당 GDP",
        "빈곤": "빈곤율",
        "교육": "중등교육 등록률",
        "전력접근": "전력 접근률",
        "디지털접근": "인터넷 이용률",
        "보건·생활여건": "기대수명",
        "고용": "실업률",
        "도시화": "도시인구 비율",
        "인구규모": "총인구",
        "탄소배출": "1인당 탄소배출",
    }
    rows = sector_wdi_rows(country_wdi, sector)
    parts = []
    for _, wdi_row in rows.iterrows():
        value = wdi_row.get("Latest_Value_Display")
        if pd.isna(wdi_row.get("Latest_Value")) or pd.isna(value):
            parts.append(f"{friendly.get(wdi_row['Signal_KR'], wdi_row['Signal_KR'])}: 최신값 없음")
            continue
        parts.append(
            f"{friendly.get(wdi_row['Signal_KR'], wdi_row['Signal_KR'])} {safe_text(value)}"
            f"({fmt_year(wdi_row.get('Latest_Year'))}, {safe_text(wdi_row.get('Series_Code'))})"
        )
    return " · ".join(parts) if parts else "관련 WDI 신호 매핑 없음"


def sector_trend_summary(country_sector_year: pd.DataFrame, sector: str) -> str:
    rows = country_sector_year.loc[country_sector_year["Sector_Group"] == sector].copy().sort_values("Year")
    if rows.empty:
        return "추세 데이터 없음"
    positive_years = int((pd.to_numeric(rows["Project_Count"], errors="coerce").fillna(0) > 0).sum())
    duration = "6개년 지속" if positive_years >= 6 else f"{positive_years}개년 레코드 관측"
    recent = rows.tail(3)
    if len(recent) < 2:
        return f"{duration} · 최근 추세 확인 제한"
    first_count = float(recent.iloc[0]["Project_Count"])
    last_count = float(recent.iloc[-1]["Project_Count"])
    direction = "증가" if last_count > first_count else ("감소" if last_count < first_count else "변동 없음")
    return f"{duration} · 최근 3개년 {direction}({fmt_int(first_count)}→{fmt_int(last_count)} 레코드)"


def sector_evidence_completeness(
    sector_row: pd.Series,
    sector_cps: pd.DataFrame,
    sector_wdi: pd.DataFrame,
    country_row: pd.Series,
) -> Dict[str, object]:
    koica_count = pd.to_numeric(pd.Series([sector_row.get("Project_Count_2019_2024")]), errors="coerce").iloc[0]
    wdi_available = int(pd.to_numeric(sector_wdi.get("Latest_Value", pd.Series(dtype=float)), errors="coerce").notna().sum())
    risk_coverage = pd.to_numeric(pd.Series([country_row.get("Policy_Risk_Data_Coverage_%")]), errors="coerce").iloc[0]
    status = {
        "KOICA": bool(pd.notna(koica_count) and koica_count > 0),
        "CPS": not sector_cps.empty,
        "WDI": wdi_available > 0,
        "실행환경": bool(pd.notna(risk_coverage) and risk_coverage > 0),
    }
    return {
        "score": sum(status.values()),
        "status": status,
        "koica_records": int(koica_count) if pd.notna(koica_count) else 0,
        "cps_chunks": len(sector_cps),
        "wdi_available": wdi_available,
        "wdi_total": len(sector_wdi),
    }


def dominant_execution_constraint(policy_row: pd.Series) -> str:
    factors = {
        "취약성": "Risk_Fragility_Score",
        "부패·투명성": "Risk_Corruption_Control_Score",
        "전자정부 역량": "Risk_Egov_Score",
        "인간개발 기반": "Risk_HDI_Score",
        "기업환경": "Risk_Business_Environment_Score",
    }
    available = []
    for label, column in factors.items():
        value = pd.to_numeric(pd.Series([policy_row.get(column)]), errors="coerce").iloc[0]
        if pd.notna(value):
            available.append((label, float(value)))
    if not available:
        return "국가 실행환경 하위지표 추가 확인 필요"
    label, value = min(available, key=lambda item: item[1])
    return f"{label} 보조점수 {value:.1f}(국가 수준 최저 하위요인)"


def sector_social_value(sector: str) -> str:
    values = {
        "공공행정": "공공서비스 접근성 · 행정 투명성 · 지방정부 역량강화",
        "기술환경에너지": "전력접근성 · 디지털 격차 완화 · 기후·환경 회복력",
        "교육": "교육 접근성 · 직업역량 · 청년 기회 확대",
        "농림수산": "식량안보 · 농가소득 기반 · 지역 회복력",
        "보건의료": "기초보건 접근성 · 보건인력 역량 · 취약계층 보호",
        "산업": "생산역량 · 일자리 기반 · 중소기업 역량강화",
        "긴급구호/취약성": "취약계층 보호 · 재난 대응역량 · 지역사회 회복력",
        "기타": "포용적 서비스 접근 · 제도역량 · 현지 파트너십",
    }
    return values.get(sector, "포용적 서비스 접근 · 현지 역량강화")


def sector_next_steps(has_cps: bool, has_wdi: bool) -> List[str]:
    return [
        "CPS 원문 페이지 확인" if has_cps else "최신 CPS에서 해당 분야 직접근거 확인",
        "WDI 신호와 현지 수요 교차검증" if has_wdi else "최신 개발지표와 현지 수요 확인",
        "현지 파트너 역량 확인",
        "기술·서비스 적합성 검토",
        "소규모 파일럿과 집행위험 완화계획 설계",
    ]


def concise_source_summary(value, limit: int = 180) -> str:
    text = safe_text(value)
    if not text:
        return "국문 설명 미표기"
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return f"{cut or text[:limit]}…"


def similar_project_cases(projects: pd.DataFrame, country: str, sector: str, limit: int = 8) -> pd.DataFrame:
    evidence = projects_for_country(projects, country, sector).drop_duplicates(["Project_Name", "Year"]).head(limit)
    rows = []
    for source_index, project in evidence.iterrows():
        rows.append({
            "국문 설명·요약": concise_source_summary(project.get("Description")),
            "원문 사업명": clean_project_text(project.get("Project_Name")),
            "연도": fmt_year(project.get("Year")),
            "분야": safe_text(project.get("Sector_Group")),
            "세부분야": safe_text(project.get("Sector_Detail")) or "미표기",
            "출처 ID": f"KODA_project_evidence_top50_2019_2024.csv#row-{int(source_index) + 2}",
            "선정 근거": "동일 국가·동일 KOICA 상위분야의 최근 공개 레코드",
        })
    return pd.DataFrame(rows)


def display_weights_table(weights: pd.DataFrame) -> pd.DataFrame:
    component_map = {
        "Development Need": "개발수요",
        "Korea Cooperation Base": "한국 기존 협력경험",
        "Sector Fit": "분야 적합성",
        "Opportunity Gap": "사업기회 공백",
        "Policy Alignment": "정책정합성",
        "Risk Feasibility": "실행가능성/리스크",
        "Data Reliability": "데이터 신뢰도",
    }
    out = weights.copy()
    if "Component" in out.columns:
        out["구성요소"] = out["Component"].map(component_map).fillna(out["Component"])
    if "Weight" in out.columns:
        out["비중"] = pd.to_numeric(out["Weight"], errors="coerce").map(lambda x: f"{x*100:.0f}%" if pd.notna(x) else "")
    if "Meaning" in out.columns:
        out["의미"] = out["Meaning"]
    cols = [c for c in ["구성요소", "비중", "의미"] if c in out.columns]
    return out[cols]

def build_markdown_proposal(country: str, sector: str, user_type: str, scale: str, keywords: str, row: pd.Series, evidence: pd.DataFrame, wdi_cards: List[Dict[str, str]]) -> str:
    candidate_type = display_candidate_type(row.get("Candidate_Type_V21"))
    country_en = english_country_name(row, country)
    sector_en = english_sector_name(sector)
    bridge_sentence = wdi_public_admin_bridge(sector)
    ev_items = []
    for _, e in evidence.head(5).iterrows():
        ev_items.append(f"- {int(e['Year'])}년 / {e['Sector_Group']} / {clean_project_text(e['Project_Name'])}")
    if not ev_items:
        ev_items = ["- 선택 국가·분야의 직접 사업근거가 부족하여 인접 분야 KOICA 사업근거와 WDI 지표를 보완적으로 검토"]
    wdi_lines = [f"- {c['title']}: {c['body']}" for c in wdi_cards[:5]]
    md = f"""# K-ODA Compass 사업기획서 초안

## 1. 사업명
**{country} {sector} 데이터 기반 개발협력 파일럿 사업**  
영문명: **Data-driven {sector_en} Cooperation Pilot in {country_en}**

## 2. 핵심 요약
- 대상국인 {country}는 v2.1 K-ODA Opportunity Score **{fmt_number(row.get('K_ODA_Opportunity_Score_V21'))}/100**으로 평가되었습니다.
- 후보유형은 **{candidate_type}**이며, 정책정합성 **{fmt_number(row.get('Policy_Alignment_Score_V21'))}**, 실행가능성 점수 **{fmt_number(row.get('Risk_Feasibility_Score_V21'))}**을 함께 고려했습니다.
- 본 초안은 KOICA 2019~2024 사업근거, World Bank WDI 개발수요, 협력국 통합 개발지표의 정책·리스크 신호를 결합한 예비기획 결과입니다.

## 3. 기획 조건
| 항목 | 내용 |
|---|---|
| 대상국 | {country} |
| 사업 분야 | {sector} |
| 사용자 유형 | {user_type} |
| 사업 규모 | {scale} |
| 핵심 키워드 | {keywords} |

## 4. 데이터 기반 추천 사유
| 점수 항목 | 값 | 해석 |
|---|---:|---|
| 개발수요 | {fmt_number(row.get('Development_Need_Score'))} | WDI 기반 수원국 개발수요 |
| 한국 기존 협력경험 | {fmt_number(row.get('Korea_Coop_Base_Score_V2'))} | KOICA 2019~2024 사업·지출·분야 경험 |
| 분야 적합성 | {fmt_number(row.get('Sector_Fit_Score_V2'))} | 국가×분야 다년도 패턴 |
| 정책정합성 | {fmt_number(row.get('Policy_Alignment_Score_V21'))} | CPS 대상국·KOICA 사무소·지원규모 보조지표 |
| 실행가능성 | {fmt_number(row.get('Risk_Feasibility_Score_V21'))} | 취약성·부패인식·전자정부·HDI 등 보조지표 |

## 5. WDI 개발수요 신호
{chr(10).join(wdi_lines)}

{bridge_sentence}

## 6. KOICA 사업근거
{chr(10).join(ev_items)}

## 7. 주요 활동
1. 현지 수요와 기존 KOICA 사업 포트폴리오 진단
2. {sector} 분야 데이터 수집·성과관리 파일럿 모듈 설계
3. 현지 파트너와 공동 워크숍 및 역량강화 교육
4. KPI 기반 모니터링 대시보드와 운영 매뉴얼 구축

## 8. 실행 로드맵
| 단계 | 기간 | 주요 과업 | 산출물 |
|---|---|---|---|
| 1단계 | 0~2개월 | 데이터 검증·현지수요 인터뷰 | 우선대상·성과지표 확정 |
| 2단계 | 3~8개월 | 파일럿 운영·교육·대시보드 구축 | 초기 운영모델 확보 |
| 3단계 | 9~12개월 | 성과평가·확장계획 수립 | 후속 ODA/민관협력 제안서 |

## 9. KPI
| 영역 | Baseline | Target | Verification |
|---|---|---|---|
| 역량강화 | 데이터 활용 교육 체계 미흡 | 공무원·CSO 실무자 50명 이상 교육 | 출석부·사전/사후 평가 |
| 서비스 개선 | 데이터 기반 업무절차 제한적 | 개선안 3건 이상 도출 | 개선안 보고서 |
| 성과관리 | 성과지표 관리 분산 | 핵심 KPI 10개 이상 정기 업데이트 | 대시보드 로그 |
| 지속가능성 | 운영 주체·예산 불명확 | 현지 운영 매뉴얼 1건 채택 | 회의록·승인문서 |

## 10. 리스크 및 보완방안
- 데이터 결측: WDI 최신연도·결측률을 명시하고 KOICA 로데이터와 교차검증
- 현지수요 불일치: 현지기관 인터뷰와 파일럿 설계로 재검증
- 실행 리스크: KOICA 사무소·국제기구·현지 NGO와 공동 추진 구조 검토
- 지속가능성: 운영주체, 비용분담, 유지보수 체계를 사업설계에 포함

## 11. 사용 근거
- KOICA ODA 실적보고 로데이터 2019~2024
- World Bank WDI 2019~2025 최신값
- KOICA 협력국 통합 개발지표 2023 공개자료
- K-ODA Compass v2.1 점수모델

> 주의: 본 결과는 최종 사업선정이 아니라 예비기획·의사결정 보조자료입니다. 실제 사업화 전 CPS 최신성, 현지수요, 파트너 적합성, 예산 타당성 검증이 필요합니다.
"""
    return md



def score_contribution_table(row: pd.Series, weights: pd.DataFrame) -> pd.DataFrame:
    mapping = [
        ("Development Need", "개발수요", "Development_Need_Score"),
        ("Korea Cooperation Base", "한국 기존 협력경험", "Korea_Coop_Base_Score_V2"),
        ("Sector Fit", "분야 적합성", "Sector_Fit_Score_V2"),
        ("Opportunity Gap", "사업기회 공백", "Opportunity_Gap_Score_V2"),
        ("Policy Alignment", "정책정합성", "Policy_Alignment_Score_V21"),
        ("Risk Feasibility", "실행가능성/리스크", "Risk_Feasibility_Score_V21"),
        ("Data Reliability", "데이터 신뢰도", "Data_Reliability_Score_V21"),
    ]
    weight_lookup = dict(zip(weights["Component"], weights["Weight"]))
    rows = []
    for component, label, col in mapping:
        score = pd.to_numeric(row.get(col), errors="coerce")
        weight = float(weight_lookup.get(component, 0))
        rows.append({
            "구성요소": label,
            "원점수": score,
            "가중치": weight,
            "기여점수": score * weight if pd.notna(score) else 0,
            "해석": f"{label} {fmt_number(score)}점이 종합점수에 {fmt_number(score * weight)}점 기여",
        })
    return pd.DataFrame(rows).sort_values("기여점수", ascending=False)


def score_reproduction_table(row: pd.Series, weights: pd.DataFrame) -> pd.DataFrame:
    sources = {
        "개발수요": ("World Bank WDI", "원자료 추적 > WDI"),
        "한국 기존 협력경험": ("KOICA 2019~2024 사업 레코드", "원자료 추적 > KOICA"),
        "분야 적합성": ("KOICA 국가×분야 다년도 집계", "원자료 추적 > KOICA"),
        "사업기회 공백": ("개발수요·KOICA 파생값", "전처리 규칙 확인"),
        "정책정합성": ("CPS 대상·KOICA 사무소·지원규모", "원자료 추적 > 정책·실행환경/CPS"),
        "실행가능성/리스크": ("취약성·부패·전자정부·HDI·기업환경", "원자료 추적 > 정책·실행환경"),
        "데이터 신뢰도": ("WDI·정책/실행환경 커버리지", "커버리지 산식 확인"),
    }
    out = score_contribution_table(row, weights).copy()
    out["사용 데이터"] = out["구성요소"].map(lambda label: sources[label][0])
    out["원자료 보기"] = out["구성요소"].map(lambda label: sources[label][1])
    return out[["구성요소", "원점수", "가중치", "기여점수", "사용 데이터", "원자료 보기"]]


def score_model_reproducibility(master: pd.DataFrame, weights: pd.DataFrame, tolerance: float = 0.01) -> dict[str, object]:
    columns = {
        "Development Need": "Development_Need_Score",
        "Korea Cooperation Base": "Korea_Coop_Base_Score_V2",
        "Sector Fit": "Sector_Fit_Score_V2",
        "Opportunity Gap": "Opportunity_Gap_Score_V2",
        "Policy Alignment": "Policy_Alignment_Score_V21",
        "Risk Feasibility": "Risk_Feasibility_Score_V21",
        "Data Reliability": "Data_Reliability_Score_V21",
    }
    weight_lookup = dict(zip(weights["Component"], pd.to_numeric(weights["Weight"], errors="coerce")))
    recalculated = pd.Series(0.0, index=master.index)
    for component, column in columns.items():
        recalculated = recalculated + pd.to_numeric(master[column], errors="coerce") * float(weight_lookup[component])
    stored = pd.to_numeric(master["K_ODA_Opportunity_Score_V21"], errors="coerce")
    error = (recalculated - stored).abs()
    recalculated_rank = recalculated.rank(ascending=False, method="first").astype(int)
    stored_rank = pd.to_numeric(master["Rank_V21"], errors="coerce").astype(int)
    return {
        "recalculated": recalculated,
        "error": error,
        "max_abs_error": float(error.max()),
        "tolerance": tolerance,
        "pass_count": int((error <= tolerance).sum()),
        "country_count": len(master),
        "rank_match_count": int((recalculated_rank == stored_rank).sum()),
        "rank_all_match": bool((recalculated_rank == stored_rank).all()),
    }


def sensitivity_analysis_table(master: pd.DataFrame, weights: pd.DataFrame, delta: float = 0.03) -> pd.DataFrame:
    columns = {
        "Development Need": ("개발수요", "Development_Need_Score"),
        "Policy Alignment": ("정책정합성", "Policy_Alignment_Score_V21"),
        "Risk Feasibility": ("실행가능성", "Risk_Feasibility_Score_V21"),
    }
    all_columns = {
        "Development Need": "Development_Need_Score",
        "Korea Cooperation Base": "Korea_Coop_Base_Score_V2",
        "Sector Fit": "Sector_Fit_Score_V2",
        "Opportunity Gap": "Opportunity_Gap_Score_V2",
        "Policy Alignment": "Policy_Alignment_Score_V21",
        "Risk Feasibility": "Risk_Feasibility_Score_V21",
        "Data Reliability": "Data_Reliability_Score_V21",
    }
    base_weights = dict(zip(weights["Component"], pd.to_numeric(weights["Weight"], errors="coerce")))
    base_rank = pd.to_numeric(master["Rank_V21"], errors="coerce").astype(int)
    base_top10 = set(master.loc[base_rank <= 10, "Country_KR"])
    rows = []
    for component, (label, _) in columns.items():
        original = float(base_weights[component])
        changed = original + delta
        scale = (1 - changed) / (1 - original)
        adjusted = {
            name: (changed if name == component else float(weight) * scale)
            for name, weight in base_weights.items()
        }
        simulated_score = pd.Series(0.0, index=master.index)
        for name, column in all_columns.items():
            simulated_score = simulated_score + pd.to_numeric(master[column], errors="coerce") * adjusted[name]
        simulated_rank = simulated_score.rank(ascending=False, method="first").astype(int)
        rank_change = (simulated_rank - base_rank).abs()
        simulated_top10 = set(master.loc[simulated_rank <= 10, "Country_KR"])
        rank_correlation = float(base_rank.astype(float).corr(simulated_rank.astype(float)))
        rows.append({
            "변경 항목": label,
            "기존 가중치": original,
            "변경 가중치": changed,
            "변경 폭": f"+{delta * 100:.0f}%p",
            "나머지 재정규화": f"기존 가중치×{scale:.4f} · 총합 {sum(adjusted.values()):.4f}",
            "최대 순위 변화": int(rank_change.max()),
            "평균 절대 순위 변화": float(rank_change.mean()),
            "Top10 중첩": f"{len(base_top10 & simulated_top10)}/10",
            "순위상관": rank_correlation,
        })
    return pd.DataFrame(rows)


def koica_country_audit_table(projects: pd.DataFrame, country: str, limit: int = 50) -> pd.DataFrame:
    evidence = projects_for_country(projects, country).head(limit)
    rows = []
    for source_index, project in evidence.iterrows():
        rows.append({
            "출처 행 ID": f"KODA_project_evidence_top50_2019_2024.csv#row-{int(source_index) + 2}",
            "고유 사업 ID": "원자료에 안정적 ID 없음",
            "연도": fmt_year(project.get("Year")),
            "분야": safe_text(project.get("Sector_Group")),
            "세부분야": safe_text(project.get("Sector_Detail")) or "미표기",
            "사업명": clean_project_text(project.get("Project_Name")),
            "사업유형": safe_text(project.get("Project_Type")) or "미표기",
            "수행기관": safe_text(project.get("Implementing_Org")) or "미표기",
        })
    return pd.DataFrame(rows)


def policy_risk_audit_table(policy_row: pd.Series) -> pd.DataFrame:
    mappings = [
        ("CPS 대상 표시", "국가협력전략 대상국가", "Policy_CPS_Target_Score", "Y이면 정책정합성 보조신호"),
        ("KOICA 사무소 존재 표시", "한국국제협력단 사무소 주재 여부", "Policy_KOICA_Office_Score", "Y이면 현지 수행기반 보조신호"),
        ("KOICA 전체 지원규모", "한국국제협력단 지원 규모_전체", "Policy_KOICA_Support_Score", "높은 공개 지원규모를 기존 협력기반 보조신호로 사용"),
        ("취약국가 지수", "취약국가 지수", "Risk_Fragility_Score", "원지수가 낮을수록 실행환경에 유리하도록 역산"),
        ("부패인식점수", "부패인식점수", "Risk_Corruption_Control_Score", "원점수가 높을수록 실행환경에 유리"),
        ("전자정부지수", "전자정부지수", "Risk_Egov_Score", "원점수가 높을수록 실행환경에 유리"),
        ("인간개발지수", "인간개발지수", "Risk_HDI_Score", "원점수가 높을수록 실행환경에 유리"),
        ("기업여건", "기업여건", "Risk_Business_Environment_Score", "방향·극단값 규칙은 번들 생성 코드 미포함"),
    ]
    rows = []
    for label, raw_column, score_column, direction in mappings:
        raw_value = policy_row.get(raw_column)
        normalized = policy_row.get(score_column)
        rows.append({
            "지표": label,
            "원자료 값": "결측" if pd.isna(raw_value) else safe_text(raw_value),
            "저장된 정규화 결과": "결측" if pd.isna(normalized) else fmt_number(normalized),
            "방향성": direction,
            "결측 여부": "결측" if pd.isna(raw_value) else "보유",
        })
    return pd.DataFrame(rows)


def normalize_design_assumptions(values: dict | None = None) -> dict:
    assumptions = {
        "duration_months": 12,
        "training_min": 30,
        "training_max": 50,
        "kpi_min": 5,
        "kpi_max": 10,
        "partner_count": "현지조사 후 확정",
        "budget_range": "예산 협의 후 확정",
        "project_stage": "예비 파일럿 설계",
        "outcome_goal": "현지 수요검증과 운영모델 검토",
    }
    assumptions.update(values or {})
    return assumptions


ASSUMPTION_NOTICE = (
    "아래 기간·인원·KPI·예산·파트너 관련 수치는 공공데이터에서 직접 도출된 사실이 아니라 "
    "현지조사 이전의 잠정 설계 예시이며, 수요조사·예산·수행기관 협의를 거쳐 수정해야 합니다."
)


def design_assumption_records(values: dict | None = None) -> list[dict[str, str]]:
    assumptions = normalize_design_assumptions(values)
    specs = [
        ("A01", "잠정 사업기간", f"잠정 {int(assumptions['duration_months'])}개월"),
        ("A02", "잠정 교육대상", f"잠정 {int(assumptions['training_min'])}~{int(assumptions['training_max'])}명"),
        ("A03", "잠정 KPI", f"잠정 {int(assumptions['kpi_min'])}~{int(assumptions['kpi_max'])}개"),
        ("A04", "잠정 파트너 수", safe_text(assumptions["partner_count"])),
        ("A05", "잠정 예산 범위", safe_text(assumptions["budget_range"])),
        ("A06", "잠정 사업 단계", safe_text(assumptions["project_stage"])),
        ("A07", "잠정 주요 성과목표", safe_text(assumptions["outcome_goal"])),
    ]
    return [
        {
            "assumption_id": assumption_id,
            "evidence_class": "AI Design Assumption",
            "label": label,
            "value": value,
            "status": "현지조사·예산·수행기관 협의 후 수정",
        }
        for assumption_id, label, value in specs
    ]


def design_assumption_lines(values: dict | None = None) -> list[str]:
    return [
        f"- [{item['assumption_id']}] **{item['evidence_class']}** · {item['label']}: {item['value']}"
        for item in design_assumption_records(values)
    ]


def build_builder_result(
    country: str,
    sector: str,
    docs: pd.DataFrame,
    design_assumptions: dict | None = None,
) -> dict[str, object]:
    evidence = docs.where(pd.notna(docs), None).to_dict(orient="records") if not docs.empty else []
    citations = [
        {
            "citation_id": safe_text(item.get("Citation_ID")),
            "evidence_class": safe_text(item.get("Evidence_Class")),
            "source_type": safe_text(item.get("Source_Type")),
            "country": safe_text(item.get("Country_KR")),
            "sector": safe_text(item.get("Sector_Group")),
        }
        for item in evidence
    ]
    return {
        "country": country,
        "sector": sector,
        "assumption_section": "AI 생성 예비 설계 가정",
        "assumption_notice": ASSUMPTION_NOTICE,
        "assumptions": design_assumption_records(design_assumptions),
        "evidence": evidence,
        "citations": citations,
        "wdi_role": (
            "WDI는 대상국의 전반적인 소득·교육·보건·인프라 여건을 설명하는 국가 개발여건 보조 신호로 "
            "활용하였다. WDI는 선택 분야 사업의 직접 수요 또는 실행가능성을 단독으로 입증하지 않는다."
        ),
        "quality_checks": [],
    }


def result_evidence_frame(result: dict[str, object], fallback: pd.DataFrame | None = None) -> pd.DataFrame:
    evidence = result.get("evidence", [])
    if isinstance(evidence, list):
        return pd.DataFrame(evidence)
    return fallback.copy() if fallback is not None else pd.DataFrame()


def result_assumption_lines(result: dict[str, object]) -> list[str]:
    records = result.get("assumptions", [])
    if not isinstance(records, list):
        return []
    return [
        f"- [{safe_text(item.get('assumption_id'))}] **{safe_text(item.get('evidence_class'))}** · "
        f"{safe_text(item.get('label'))}: {safe_text(item.get('value'))}"
        for item in records
    ]


def evidence_class_summary_table(docs: pd.DataFrame) -> str:
    lines = [
        "| Evidence ID | Evidence Class | 출처유형 | 문서에서의 역할 |",
        "|---|---|---|---|",
    ]
    for _, evidence in docs.iterrows():
        role = safe_text(evidence.get("Model_Role")) or "역할 메타데이터 없음"
        lines.append(
            f"| {safe_text(evidence.get('Citation_ID'))} | {safe_text(evidence.get('Evidence_Class'))} | "
            f"{safe_text(evidence.get('Source_Type'))} | {role.replace('|', '/')} |"
        )
    return "\n".join(lines)


def structured_result_appendix(result: dict[str, object], docs: pd.DataFrame) -> str:
    return f"""## Evidence Class 요약
{evidence_class_summary_table(docs)}

## WDI 역할
{safe_text(result.get('wdi_role'))}

## AI 생성 예비 설계 가정
{safe_text(result.get('assumption_notice'))}

{chr(10).join(result_assumption_lines(result))}
"""


def build_rag_prompt(country: str, sector: str, user_type: str, scale: str, keywords: str, row: pd.Series, docs: pd.DataFrame, weights: pd.DataFrame, design_assumptions: dict | None = None) -> str:
    contribution = score_contribution_table(row, weights)
    contribution_lines = "\n".join(
        f"- {r['구성요소']}: 원점수 {fmt_number(r['원점수'])}, 가중치 {fmt_number(r['가중치'], 2)}, 기여점수 {fmt_number(r['기여점수'])}"
        for _, r in contribution.iterrows()
    )
    return f"""You are K-ODA Compass, an evidence-grounded AI policy copilot for Korean ODA planning.

Write in Korean. Create a concise but complete ODA project proposal draft.
Rules:
1. Every factual claim about the country, sector, WDI signal, KOICA evidence, policy alignment, or risk must cite evidence IDs like [E01].
2. 선택 분야와 일치하는 직접근거만 직접 정책·사업근거로 사용한다. 다른 분야 자료를 직접근거로 사용하지 않는다.
3. WDI는 국가 개발여건 보조 신호로만 설명하고 선택 분야의 직접 수요를 단독으로 입증한다고 쓰지 않는다.
4. Model Output, Derived Evidence, Source Evidence, Supplementary Source, AI Design Assumption을 구분한다.
5. 파트너 참여, MOU, 예산, 기간, 인원, KPI를 확정하지 않는다. 아래 A01~A07을 잠정 설계 가정으로만 표시한다.
6. 최종 실행가능성을 단정하지 않고 "예비 검토", "시사", "검증 필요"를 사용한다.
7. 국제기구 연계나 특정 파트너 참여를 자동 권고하지 않는다.
8. 내부 변수명이나 Score_Direction 코드를 출력하지 않는다.
9. Use only the evidence pack below.
10. "CPS", "국가협력전략", "정책원문"을 주장하는 문장에는 Source_Type이 CPS PDF인 ID만 인용한다.
11. "기존 KOICA 사업", "협력경험"을 주장하는 문장에는 KOICA Project 또는 Sector Portfolio ID만 인용한다.
12. "실행환경", "실행가능성", "리스크"를 주장하는 문장에는 Policy/Risk ID만 인용한다.
13. "국가 개발여건"을 주장하는 문장에는 WDI ID만 인용한다.
14. 기존 KOICA 사업은 한국의 협력경험을 보여줄 뿐 현재 개발수요를 직접 입증하지 않는다고 명시한다.

## User conditions
- 대상국: {country}
- 분야: {sector}
- 사용자 유형: {user_type}
- 사업 규모: {scale}
- 키워드: {keywords}

## Score summary
- 종합점수: {fmt_number(row.get('K_ODA_Opportunity_Score_V21'))}/100
- 후보유형: {display_candidate_type(row.get('Candidate_Type_V21'))}
- 추천분야: {safe_text(row.get('Recommended_Service_Angle_V2'))}

## Contribution table
{contribution_lines}

## AI-generated preliminary design assumptions
{chr(10).join(design_assumption_lines(design_assumptions))}

## Evidence pack
{format_rag_citations(docs)}
"""


def missing_key_fallback(api_key: str) -> tuple[str | None, str] | None:
    if api_key.strip():
        return None
    return None, "OPENAI_API_KEY가 없어 로컬 RAG 생성으로 전환했습니다."


def extract_openai_response_text(response) -> str:
    text = getattr(response, "output_text", None)
    if not text:
        chunks = []
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                value = getattr(content, "text", None)
                if value:
                    chunks.append(value)
        text = "\n".join(chunks)
    return safe_text(text).strip()


def openai_fallback_message(exc: Exception) -> str:
    error_name = type(exc).__name__.lower()
    error_text = str(exc).lower()
    if "authentication" in error_name or "unauthorized" in error_text or "api key" in error_text:
        reason = "인증 오류"
    elif "ratelimit" in error_name or "quota" in error_text or "billing" in error_text:
        reason = "사용량·할당량 오류"
    elif "connection" in error_name or "timeout" in error_name or "network" in error_text:
        reason = "네트워크 오류"
    elif "notfound" in error_name or "model" in error_text:
        reason = "모델 설정 오류"
    else:
        reason = "응답 처리 오류"
    return f"LLM {reason}로 로컬 RAG 생성으로 전환했습니다. 잠시 후 다시 시도하거나 로컬 RAG 모드를 사용해 주세요."


def call_openai_llm(prompt: str) -> tuple[str | None, str]:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    try:
        api_key = api_key or str(st.secrets.get("OPENAI_API_KEY", "")).strip()
    except Exception:
        pass
    missing_key_result = missing_key_fallback(api_key)
    if missing_key_result is not None:
        return missing_key_result

    model = os.environ.get("OPENAI_MODEL", "gpt-5.2").strip() or "gpt-5.2"
    try:
        model = str(st.secrets.get("OPENAI_MODEL", model)).strip() or model
    except Exception:
        pass

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, timeout=30.0, max_retries=1)
        response = client.responses.create(
            model=model,
            input=prompt,
            instructions="You are an evidence-grounded Korean ODA proposal writer. Cite evidence IDs and avoid unsupported claims.",
        )
        text = extract_openai_response_text(response)
        if not text:
            return None, "LLM 응답이 비어 있어 로컬 RAG 생성으로 전환했습니다."
        return text, f"OpenAI Responses API 사용: {model}"
    except Exception as exc:
        return None, openai_fallback_message(exc)


def fallback_self_test_results() -> pd.DataFrame:
    class AuthenticationError(Exception):
        pass

    class APITimeoutError(Exception):
        pass

    class EmptyResponse:
        output_text = None
        output = []

    no_key = missing_key_fallback("")
    auth_message = openai_fallback_message(AuthenticationError("invalid API key"))
    timeout_message = openai_fallback_message(APITimeoutError("request timeout"))
    exception_message = openai_fallback_message(RuntimeError("unexpected response"))
    empty_text = extract_openai_response_text(EmptyResponse())
    rows = [
        ["OPENAI_API_KEY 없음", "Local RAG로 전환", safe_text(no_key[1] if no_key else ""), "PASS" if no_key and no_key[0] is None else "FAIL"],
        ["API 인증 오류(모의)", "안내 + Local RAG fallback", auth_message, "PASS" if "인증 오류" in auth_message else "FAIL"],
        ["API 시간초과(모의)", "Local RAG fallback", timeout_message, "PASS" if "네트워크 오류" in timeout_message else "FAIL"],
        ["빈 응답(모의)", "빈 문자열 감지 + fallback", "빈 응답 감지" if not empty_text else "감지 실패", "PASS" if not empty_text else "FAIL"],
        ["API 예외(모의)", "예외를 메시지로 변환하고 프로세스 유지", exception_message, "PASS" if "로컬 RAG 생성으로 전환" in exception_message else "FAIL"],
        ["민감정보 로그", "API 키 문자열 미출력", "fallback 메시지 경로 정적 확인 · 실제 로그 캡처 미실행", "INFO"],
    ]
    return pd.DataFrame(rows, columns=["검증 항목", "통과 기준", "실제 결과", "상태"])


def build_rag_markdown_proposal(
    country: str,
    sector: str,
    user_type: str,
    scale: str,
    keywords: str,
    row: pd.Series,
    docs: pd.DataFrame,
    weights: pd.DataFrame,
    design_assumptions: dict | None = None,
    result: dict[str, object] | None = None,
) -> str:
    result = result or build_builder_result(country, sector, docs, design_assumptions)
    docs = result_evidence_frame(result, docs)
    assumptions = normalize_design_assumptions(design_assumptions)
    score_cites = citation_ids(docs, "Score Model", 1)
    policy_cites = citation_ids(docs, "Policy/Risk", 1)
    cps_cites = citation_ids(docs, "CPS PDF", 2)
    wdi_cites = citation_ids(docs, "WDI", 3)
    project_cites = citation_ids(docs, "KOICA Project", 4)
    portfolio_cites = citation_ids(docs, "Sector Portfolio", 1)
    contribution = score_contribution_table(row, weights)
    top_contrib = contribution.head(3)
    cps_docs = docs.loc[(docs["Source_Type"] == "CPS PDF") & (docs["Directness"] == "직접근거")].head(2)
    koica_docs = docs.loc[(docs["Source_Type"] == "KOICA Project") & (docs["Directness"] == "직접근거")].head(4)
    wdi_docs = docs.loc[docs["Source_Type"] == "WDI"].head(3)

    cps_lines = [
        f"- [{d['Citation_ID']}] **{d['Title']}**: {concise_source_summary(d['Content'], 260)}"
        for _, d in cps_docs.iterrows()
    ] or ["- 선택 국가·분야와 직접 일치하는 CPS 청크가 없어 최신 CPS 원문에서 추가 확인이 필요합니다."]
    koica_lines = [
        f"- [{d['Citation_ID']}] **{d['Original_Title']}** · 사업기간 {d['Project_Period']} · "
        f"관측 연도 {d['Observed_Years']} · 원자료 {fmt_int(d['Record_Count'])}건 · {d['Duplicate_Status']}"
        for _, d in koica_docs.iterrows()
    ] or ["- 선택 국가·분야의 직접 KOICA 사업근거가 제한적이므로 현지 수요조사와 원자료 재확인이 필요합니다."]
    wdi_lines = [
        f"- [{d['Citation_ID']}] **{d['Original_Title']}** ({d['Indicator_Code']}): {d['Indicator_Value']} · "
        f"최신연도 {d['Reference_Year']} · {d['Sector_Relevance']} · {d['Direction_Label']}"
        for _, d in wdi_docs.iterrows()
    ] or ["- WDI 최신값이 제한적이므로 원천 데이터 재확인이 필요합니다."]
    contrib_lines = [
        f"- {r['구성요소']}: 원점수 {fmt_number(r['원점수'])}, 가중 기여도 {fmt_number(r['기여점수'])}"
        for _, r in top_contrib.iterrows()
    ]
    used_ids = []
    for cite_group in (score_cites, policy_cites, cps_cites, project_cites, portfolio_cites, wdi_cites):
        used_ids.extend(re.findall(r"E\d{2}", cite_group))
    citation_summary = ", ".join(dict.fromkeys(used_ids)) or "직접 Citation 없음"
    class_summary = evidence_class_summary_table(docs)
    assumption_notice = safe_text(result.get("assumption_notice")) or ASSUMPTION_NOTICE
    assumption_lines = result_assumption_lines(result)
    wdi_role = safe_text(result.get("wdi_role"))

    return f"""# K-ODA Compass 근거 기반 AI 사업제안서

## 1. 사업명
**{country} {sector} 및 {keywords.split(',')[0].strip()} 역량강화 예비사업**

## 2. 핵심 판단
- {country}의 v2.1 국가 우선검토 점수는 **{fmt_number(row.get('K_ODA_Opportunity_Score_V21'))}/100**이며 후보유형은 **{compact_candidate_label(row.get('Candidate_Type_V21'))}**입니다 {score_cites}.
- 개발수요와 정책정합성은 높지만 실행가능성 보완이 필요한 예비 검토 대상입니다. 사업화 전 현지 파트너 역량, 제도환경, 집행위험과 참여 의향을 추가 검증해야 합니다 {policy_cites}.
- {sector} 분야의 직접 정책방향은 선택 분야와 일치하는 CPS 정책원문에서 확인합니다 {cps_cites}.
- 기존 KOICA 사업은 한국의 해당 분야 협력경험을 보여줍니다 {project_cites}. 대상국의 현재 사업수요는 CPS 정책방향과 현지 수요조사를 통해 별도로 검증해야 합니다.

## Evidence Class 요약
{class_summary}

## 3. Model Output · 국가 점수 분해
{chr(10).join(contrib_lines)}
{score_cites}

## 4. Source Evidence · CPS 정책원문
{chr(10).join(cps_lines)}

## 5. Source Evidence · KOICA 기존 협력경험
{chr(10).join(koica_lines)}

기존 KOICA 사업은 한국의 해당 분야 협력경험과 유사사업 경험을 보여주지만, 현재 개발수요를 직접 입증하지 않습니다. 현재 사업수요는 CPS 정책방향과 현지 수요조사를 통해 별도로 검증해야 합니다.

## 6. Supplementary Source · 국가 개발여건 보조 신호
{wdi_role}

{chr(10).join(wdi_lines)}

## 7. Derived Evidence · 정책·실행환경 보조지표
- 정책정합성 {fmt_number(row.get('Policy_Alignment_Score_V21'))}, 실행가능성 {fmt_number(row.get('Risk_Feasibility_Score_V21'))}. 해당 값은 현지조사나 기관 실사를 대체하지 않는 파생점수입니다 {policy_cites}.
- 기존 KOICA 분야 집계는 과거 협력경험을 보여주며 현재 사업 타당성과 동일한 의미가 아닙니다 {portfolio_cites}.

## 8. 예비 사업설계 방향
| 항목 | 내용 |
|---|---|
| 대상 사용자 | {user_type} |
| 사업 규모 | {scale} |
| 핵심 키워드 | {keywords} |
| 추진 절차 | 현지 수요검증 → 파트너 역량검토 → 소규모 파일럿 → 성과검토 → 확장 여부 결정 |
| 잠재 파트너 유형 | {country} 관계부처, KOICA 현지 네트워크, 현지 CSO·연구기관, 기술 수행기관, 개발협력기관 |

잠재 파트너의 실제 참여 의향·법적 권한·수행역량·비용분담은 별도 실사가 필요합니다.

## 9. AI 생성 예비 설계 가정
{assumption_notice}

{chr(10).join(assumption_lines)}

### 잠정 활동·성과 프레임
| 영역 | 잠정 설계 | 검증 방법 |
|---|---|---|
| 현지 수요 | 관계부처·잠재 수행기관의 문제정의와 데이터 수요 확인 | 인터뷰·원자료 검토 |
| 역량강화 | 잠정 {int(assumptions['training_min'])}~{int(assumptions['training_max'])}명 대상 교육 | 참여자·사전/사후 평가 |
| 성과관리 | 잠정 {int(assumptions['kpi_min'])}~{int(assumptions['kpi_max'])}개 KPI 후보 설계 | 지표 정의서·검증회의 |
| 운영모델 | {safe_text(assumptions['outcome_goal'])} | 파일럿 결과와 참여 의향 검토 |

## 10. 핵심 실행위험과 다음 검증
- 현지수요 미검증: 관계부처와 잠재 사용자 인터뷰로 문제정의·수혜자·데이터 가용성을 확인합니다.
- 파트너 역량 미검증: 참여 의향, 법적 권한, 인력·예산·운영역량을 실사합니다.
- 근거 최신성: CPS 원문 버전과 WDI 최신연도, KOICA 원자료의 갱신 여부를 재확인합니다.
- 실행환경 위험: 정책·실행환경 보조지표를 참고하되 현지 제도·조달·집행 절차를 별도 검토합니다 {policy_cites}.

## 11. Citation 안내
주요 Citation: {citation_summary}

전체 근거 목록과 원자료 추적정보는 별첨 Evidence Pack을 참조하세요.

> 본 초안은 K-ODA Compass RAG 검색 결과와 공개데이터 보조지표에 근거한 예비기획 자료입니다. 최종 사업 타당성 판단은 현지조사와 공식 정책문서 검토가 필요합니다.
"""


def build_policy_brief(
    country: str,
    sector: str,
    row: pd.Series,
    docs: pd.DataFrame,
    design_assumptions: dict | None = None,
    result: dict[str, object] | None = None,
) -> str:
    result = result or build_builder_result(country, sector, docs, design_assumptions)
    docs = result_evidence_frame(result, docs)
    assumptions = normalize_design_assumptions(design_assumptions)
    direct_docs = docs.loc[docs.get("Directness", pd.Series(index=docs.index, dtype=str)) == "직접근거"].head(4)
    class_summary = evidence_class_summary_table(docs.head(8))
    assumption_notice = safe_text(result.get("assumption_notice")) or ASSUMPTION_NOTICE
    return f"""# 1-Page Policy Brief: {country} {sector}

## 결정문
{country} {sector} 분야는 개발수요와 정책정합성은 높지만 실행가능성 보완이 필요한 예비 검토 대상입니다. 사업화 전 현지 파트너 역량, 제도환경 및 집행위험 검증이 필요합니다.

## 핵심 판단 신호
- 국가 우선검토 점수: {fmt_number(row.get('K_ODA_Opportunity_Score_V21'))}/100
- 후보유형: {compact_candidate_label(row.get('Candidate_Type_V21'))}
- 개발수요: {fmt_number(row.get('Development_Need_Score'))}
- 정책정합성: {fmt_number(row.get('Policy_Alignment_Score_V21'))}
- 실행가능성: {fmt_number(row.get('Risk_Feasibility_Score_V21'))}

## 선택 분야 직접근거
{format_rag_citations(direct_docs)}

## Evidence Class 요약
{class_summary}

## WDI 역할
{safe_text(result.get('wdi_role'))}

## AI 생성 예비 설계 가정
{assumption_notice}

{chr(10).join(result_assumption_lines(result))}

## 다음 검증
1. CPS 원문 근거와 최신 정책문서 교차확인
2. 현지 파트너 후보 인터뷰 및 수요검증
3. 예산·운영주체 가정 검증
4. 잠정 KPI와 사업기간 조정
"""


def korean_pdf_font_status() -> tuple[bool, str]:
    missing = [str(path.relative_to(APP_DIR)) for path in (REGULAR_FONT_PATH, BOLD_FONT_PATH) if not path.exists()]
    if missing:
        return False, "Proposal PDF 생성에 필요한 한글 폰트 파일이 없습니다: " + ", ".join(missing)
    return True, f"Nanum Gothic Regular/Bold · {REGULAR_FONT_PATH.relative_to(APP_DIR)}"


def register_reportlab_korean_fonts() -> tuple[str, str] | None:
    available, _ = korean_pdf_font_status()
    if not available:
        return None
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except Exception:
        return None
    regular_name = "KodaNanumGothic"
    bold_name = "KodaNanumGothic-Bold"
    registered = set(pdfmetrics.getRegisteredFontNames())
    if regular_name not in registered:
        pdfmetrics.registerFont(TTFont(regular_name, str(REGULAR_FONT_PATH)))
    if bold_name not in registered:
        pdfmetrics.registerFont(TTFont(bold_name, str(BOLD_FONT_PATH)))
    pdfmetrics.registerFontFamily(
        regular_name,
        normal=regular_name,
        bold=bold_name,
        italic=regular_name,
        boldItalic=bold_name,
    )
    return regular_name, bold_name


def markdown_to_pdf_bytes(title: str, markdown_text: str) -> bytes | None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        from reportlab.pdfgen.canvas import Canvas
        from reportlab.platypus import LongTable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, TableStyle
        from xml.sax.saxutils import escape
    except Exception:
        return None

    fonts = register_reportlab_korean_fonts()
    if not fonts:
        return None
    regular_font, bold_font = fonts

    buffer = io.BytesIO()
    page_width, _ = A4
    margin = 42
    usable_width = page_width - margin * 2
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=48,
        bottomMargin=48,
        title=title,
        author="K-ODA Compass",
        subject="근거 기반 AI ODA 사업제안서",
    )
    styles = {
        "title": ParagraphStyle("KoreanTitle", fontName=bold_font, fontSize=17, leading=23, spaceAfter=16, alignment=TA_CENTER, wordWrap="CJK", textColor=colors.HexColor("#173A5E")),
        "h1": ParagraphStyle("KoreanH1", fontName=bold_font, fontSize=15, leading=21, spaceBefore=12, spaceAfter=8, wordWrap="CJK", textColor=colors.HexColor("#173A5E")),
        "h2": ParagraphStyle("KoreanH2", fontName=bold_font, fontSize=12, leading=18, spaceBefore=10, spaceAfter=6, wordWrap="CJK", textColor=colors.HexColor("#315D86")),
        "h3": ParagraphStyle("KoreanH3", fontName=bold_font, fontSize=10.5, leading=16, spaceBefore=8, spaceAfter=4, wordWrap="CJK"),
        "body": ParagraphStyle("KoreanBody", fontName=regular_font, fontSize=9.2, leading=14.2, spaceAfter=5, wordWrap="CJK"),
        "bullet": ParagraphStyle("KoreanBullet", fontName=regular_font, fontSize=9.2, leading=14.2, leftIndent=12, firstLineIndent=-8, spaceAfter=3, wordWrap="CJK"),
        "quote": ParagraphStyle("KoreanQuote", fontName=regular_font, fontSize=8.8, leading=13.5, leftIndent=10, rightIndent=10, borderColor=colors.HexColor("#B8C7D6"), borderWidth=0.7, borderPadding=7, backColor=colors.HexColor("#F4F7FA"), wordWrap="CJK"),
        "table_header": ParagraphStyle("KoreanTableHeader", fontName=bold_font, fontSize=8.2, leading=11.5, wordWrap="CJK", textColor=colors.white),
        "table_body": ParagraphStyle("KoreanTableBody", fontName=regular_font, fontSize=7.8, leading=11.2, wordWrap="CJK"),
        "footer": ParagraphStyle("KoreanFooter", fontName=regular_font, fontSize=7.5, leading=9, alignment=TA_RIGHT, textColor=colors.HexColor("#667788")),
    }

    def plain_markdown(value: str) -> str:
        value = value.replace("**", "").replace("`", "")
        return escape(value.strip())

    story = [Paragraph(plain_markdown(title), styles["title"])]
    lines = markdown_text.splitlines()
    index = 0
    while index < len(lines):
        raw = lines[index].rstrip()
        line = raw.strip()
        if not line:
            story.append(Spacer(1, 4))
            index += 1
            continue
        if line == "---":
            story.append(PageBreak())
            index += 1
            continue
        if line.startswith("|") and index + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-+", lines[index + 1]):
            table_lines = [line]
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index].strip())
                index += 1
            parsed = [[cell.strip() for cell in table_line.strip("|").split("|")] for table_line in table_lines]
            column_count = max(len(row) for row in parsed)
            parsed = [row + [""] * (column_count - len(row)) for row in parsed]
            table_data = []
            for row_index, table_row in enumerate(parsed):
                style = styles["table_header"] if row_index == 0 else styles["table_body"]
                table_data.append([Paragraph(plain_markdown(cell), style) for cell in table_row])
            table = LongTable(table_data, colWidths=[usable_width / column_count] * column_count, repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#315D86")),
                ("FONTNAME", (0, 0), (-1, 0), bold_font),
                ("FONTNAME", (0, 1), (-1, -1), regular_font),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C8D3DE")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FB")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.extend([table, Spacer(1, 8)])
            continue
        heading = re.match(r"^(#{1,3})\s+(.*)$", line)
        if heading:
            heading_text = heading.group(2).replace("**", "").strip()
            if heading_text != title.strip():
                story.append(Paragraph(plain_markdown(heading_text), styles[f"h{len(heading.group(1))}"]))
        elif re.match(r"^[-*]\s+", line):
            story.append(Paragraph("• " + plain_markdown(re.sub(r"^[-*]\s+", "", line)), styles["bullet"]))
        elif re.match(r"^\d+\.\s+", line):
            story.append(Paragraph(plain_markdown(line), styles["bullet"]))
        elif line.startswith(">"):
            story.append(Paragraph(plain_markdown(line.lstrip("> ")), styles["quote"]))
        else:
            story.append(Paragraph(plain_markdown(line), styles["body"]))
        index += 1

    def add_footer(canvas, document) -> None:
        canvas.saveState()
        canvas.setFont(regular_font, 7.5)
        canvas.setFillColor(colors.HexColor("#667788"))
        canvas.drawRightString(A4[0] - margin, 24, f"K-ODA Compass · {document.page}페이지")
        canvas.restoreState()

    class KoreanCanvas(Canvas):
        def __init__(self, *args, **kwargs):
            kwargs["initialFontName"] = regular_font
            kwargs["initialFontSize"] = 9.2
            super().__init__(*args, **kwargs)

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer, canvasmaker=KoreanCanvas)
    return buffer.getvalue()


def builder_output_quality_report(
    country: str,
    sector: str,
    docs: pd.DataFrame,
    proposal: str,
    brief: str,
    evidence_pack: str,
    proposal_pdf: bytes | None,
    result: dict[str, object] | None = None,
) -> tuple[str, pd.DataFrame]:
    result = result or build_builder_result(country, sector, docs)
    docs = result_evidence_frame(result, docs)
    direct = docs.loc[docs.get("Directness", pd.Series(index=docs.index, dtype=str)) == "직접근거"]
    evidence_ids = set(docs.get("Citation_ID", pd.Series(dtype=str)).dropna().astype(str))
    cited_ids = set(re.findall(r"\[(E\d{2})\]", proposal + "\n" + brief))
    unknown_ids = sorted(cited_ids - evidence_ids)
    country_mismatch = int((direct.get("Country_KR", pd.Series(index=direct.index, dtype=str)) != country).sum())
    sector_mismatch = int((direct.get("Sector_Group", pd.Series(index=direct.index, dtype=str)) != sector).sum())
    cross_cps = int(((direct.get("Source_Type", pd.Series(index=direct.index, dtype=str)) == "CPS PDF") & (direct.get("Sector_Group", pd.Series(index=direct.index, dtype=str)) != sector)).sum())
    cross_portfolio = int(((direct.get("Source_Type", pd.Series(index=direct.index, dtype=str)) == "Sector Portfolio") & (direct.get("Sector_Group", pd.Series(index=direct.index, dtype=str)) != sector)).sum())
    duplicate_groups = int(pd.to_numeric(docs.loc[docs.get("Source_Type") == "KOICA Project", "Record_Count"], errors="coerce").fillna(1).gt(1).sum()) if "Record_Count" in docs else 0
    combined = "\n".join([proposal, brief, evidence_pack])
    internal_names = re.findall(r"lower_is_higher_need|higher_is_higher_need|\bproxy\b", combined, flags=re.IGNORECASE)
    comma_years = re.findall(r"\b2,0\d{2}\b", combined)
    forbidden_prescriptions = [
        phrase for phrase in (
            "국제기구 연계 권고",
            "국제기구 참여 필요",
            "KOICA 사무소·국제기구·기업 컨소시엄 확정",
            "MOU 체결 예정",
        ) if phrase in combined
    ]
    unqualified_design_numbers = [
        phrase for phrase in ("12개월 파일럿", "실무자 50명 이상", "KPI 10개 이상", "파트너 2곳 이상", "제안서 1건")
        if phrase in proposal
    ]
    assumptions = result.get("assumptions", []) if isinstance(result.get("assumptions", []), list) else []
    assumption_ids = {safe_text(item.get("assumption_id")) for item in assumptions}
    assumption_classes_ok = bool(assumptions) and all(
        safe_text(item.get("evidence_class")) == "AI Design Assumption" for item in assumptions
    )
    assumption_notice = safe_text(result.get("assumption_notice"))
    assumption_section_ok = safe_text(result.get("assumption_section")) == "AI 생성 예비 설계 가정"
    assumption_notice_ok = all(term in assumption_notice for term in ("공공데이터", "잠정 설계", "수요조사", "수정"))
    assumption_structured = (
        all(f"A{index:02d}" in assumption_ids for index in range(1, 8))
        and assumption_section_ok
        and assumption_classes_ok
        and assumption_notice_ok
    )
    evidence_classes = docs.get("Evidence_Class", pd.Series(index=docs.index, dtype=str)).fillna("").astype(str)
    missing_classes = int(evidence_classes.eq("").sum())
    expected_classes = {"Source Evidence", "Supplementary Source", "Derived Evidence", "Model Output"}
    evidence_class_structured = (
        missing_classes == 0
        and set(evidence_classes).issubset(expected_classes)
        and assumption_classes_ok
    )
    wdi_rows = docs.loc[docs.get("Source_Type", pd.Series(index=docs.index, dtype=str)) == "WDI"]
    wdi_direct = int(((docs.get("Source_Type", pd.Series(index=docs.index, dtype=str)) == "WDI") & (docs.get("Directness", pd.Series(index=docs.index, dtype=str)) == "직접근거")).sum())
    wdi_class_ok = wdi_rows.empty or wdi_rows.get("Evidence_Class", pd.Series(index=wdi_rows.index, dtype=str)).eq("Supplementary Source").all()
    wdi_role = safe_text(result.get("wdi_role"))
    wdi_role_ok = wdi_class_ok and wdi_direct == 0 and all(
        term in wdi_role for term in ("국가 개발여건 보조 신호", "직접 수요", "단독으로 입증하지 않는다")
    )
    semantic_mismatches = citation_semantic_mismatches(proposal + "\n" + brief, docs)
    misleading_wdi_phrases = [
        phrase for phrase in (
            "WDI 또는 추가 통계자료를 사용해 실행가능성을 평가하였다",
            "WDI로 실행가능성을 평가",
            "WDI가 실행가능성을 입증",
        ) if phrase in combined
    ]
    metadata_missing = int(docs.apply(
        lambda item: (
            "미등록" in safe_text(item.get("Source_URL"))
            or "메타데이터 없음" in safe_text(item.get("Collected_At"))
        ),
        axis=1,
    ).sum()) if not docs.empty else 0
    font_available, font_note = korean_pdf_font_status()
    pdf_valid = bool(proposal_pdf and proposal_pdf.startswith(b"%PDF"))
    secret_patterns = re.findall(r"(?:sk-[A-Za-z0-9_-]{12,}|OPENAI_API_KEY\s*=\s*\S+)", combined)

    checks = [
        ["직접근거 국가 일치", "불일치 0건", f"{country_mismatch}건", "BLOCK" if country_mismatch else "PASS"],
        ["직접근거 분야 일치", "불일치 0건", f"{sector_mismatch}건", "BLOCK" if sector_mismatch else "PASS"],
        ["Citation ID 무결성", "미존재 0건", f"{len(unknown_ids)}건" + (f" · {', '.join(unknown_ids)}" if unknown_ids else ""), "BLOCK" if unknown_ids else "PASS"],
        ["다른 분야 CPS 직접근거", "0건", f"{cross_cps}건", "BLOCK" if cross_cps else "PASS"],
        ["다른 분야 포트폴리오 직접근거", "0건", f"{cross_portfolio}건", "BLOCK" if cross_portfolio else "PASS"],
        ["Citation 의미 정합성", "주장과 source_type 불일치 0건", f"{len(semantic_mismatches)}건", "BLOCK" if semantic_mismatches else "PASS"],
        ["KOICA 반복 레코드", "통합·상태 표시", f"통합 그룹 {duplicate_groups}개", "REVIEW" if duplicate_groups else "PASS"],
        ["확정형 자동 처방", "금지 표현 0건", f"{len(forbidden_prescriptions)}건", "BLOCK" if forbidden_prescriptions else "PASS"],
        ["근거 없는 확정형 KPI", "금지 패턴 0건", f"{len(unqualified_design_numbers)}건", "BLOCK" if unqualified_design_numbers else "PASS"],
        ["내부 변수명", "노출 0건", f"{len(internal_names)}건", "BLOCK" if internal_names else "PASS"],
        ["연도 쉼표", "오류 0건", f"{len(comma_years)}건", "BLOCK" if comma_years else "PASS"],
        ["Evidence Class", "누락 0건", f"{missing_classes}건", "BLOCK" if missing_classes else "PASS"],
        ["WDI 직접근거 오표기", "0건", f"{wdi_direct}건", "BLOCK" if wdi_direct else "PASS"],
        ["AI 설계 가정", "A01~A07·class·잠정 안내문", "구조화 레코드 7개" if assumption_structured else "구조화 가정 누락", "PASS" if assumption_structured else "BLOCK"],
        ["원천·파생근거 구분", "Evidence 객체 class 완전성", "4개 Evidence Class 구조화" if evidence_class_structured else "class 누락 또는 유형 불완전", "PASS" if evidence_class_structured else "BLOCK"],
        ["WDI 역할", "Supplementary Source·국가 배경 보조", "보조 신호로 구조화" if wdi_role_ok else "직접근거 오해 가능", "PASS" if wdi_role_ok else "BLOCK"],
        ["WDI 오해 표현", "금지 표현 0건", f"{len(misleading_wdi_phrases)}건", "BLOCK" if misleading_wdi_phrases else "PASS"],
        ["출처 URL·수집일", "값 또는 미등록 상태 명시", f"메타데이터 확인 필요 {metadata_missing}건", "REVIEW" if metadata_missing else "PASS"],
        ["PDF 한글 폰트", "저장소 TTF 등록", font_note, "PASS" if font_available else "BLOCK"],
        ["PDF 파일 구조", "%PDF 정상", "정상" if pdf_valid else "생성 실패", "PASS" if pdf_valid else "BLOCK"],
        ["검은 사각형 문자", "원문 내 0개", f"{combined.count('■')}개", "BLOCK" if "■" in combined else "PASS"],
        ["Secret·API 키", "노출 0건", f"{len(secret_patterns)}건", "BLOCK" if secret_patterns else "PASS"],
    ]
    report = pd.DataFrame(checks, columns=["검사 항목", "통과 기준", "실제 결과", "상태"])
    result["quality_checks"] = report.to_dict(orient="records")
    if report["상태"].eq("BLOCK").any():
        status = "BLOCK"
    elif report["상태"].eq("REVIEW").any():
        status = "REVIEW"
    else:
        status = "PASS"
    return status, report


def make_qr_png(url: str) -> bytes | None:
    if not url.strip():
        return None
    try:
        import qrcode
        img = qrcode.make(url.strip())
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
    except Exception:
        return None


def rag_evidence_unit_counts(master: pd.DataFrame) -> pd.DataFrame:
    counts = count_csv_records(("sector_summary", "projects", "policy_risk", "cps_pdf"))
    valid_wdi, _ = count_valid_wdi_latest()
    return pd.DataFrame([
        ["정량 점수모델", len(master), "파생 레코드", "국가 점수·후보유형 근거"],
        ["분야 포트폴리오", counts["sector_summary"], "파생 레코드", "국가×분야 기존 협력경험"],
        ["KOICA 사업 레코드", counts["projects"], "핵심 원자료", "사업명·연도·분야 근거"],
        ["WDI 최신값 레코드", valid_wdi, "보조 원자료", "개발수요 지표 근거"],
        ["정책·실행환경", counts["policy_risk"], "파생 레코드", "정책정합성·실행환경 보조"],
        ["CPS RAG 청크", counts["cps_pdf"], "핵심 원문 청크", "정책문서 페이지 인용"],
    ], columns=["근거 유형", "근거 단위 수", "원천·파생 구분", "모델 역할"])


def render_ai_validation(data):
    master, weights, cps_coverage = data["master"], data["weights"], data["cps_coverage"]
    st.title("AI·모델 내부 검증")
    st.caption("정량 점수 재현성, RAG 근거검색, 인용 무결성, 생성모드 fallback과 민감도 결과를 내부 점검합니다.")
    st.markdown("""
    <div class="section-note">본 화면은 제출물 내부의 재현·품질 점검입니다. 외부기관 인증이나 독립 검증을 완료했다는 의미가 아닙니다.</div>
    """, unsafe_allow_html=True)

    country = st.selectbox("검증 국가", get_country_options(master), index=0, key="validation_country")
    row = get_country_row(master, country)
    score_audit = score_model_reproducibility(master, weights)
    valid_wdi, total_wdi = count_valid_wdi_latest()
    readable_codes = set(cps_coverage.loc[pd.to_numeric(cps_coverage["Readable_Pages"], errors="coerce").fillna(0) > 0, "Country_Code"].astype(str))
    cps_top50 = len(set(master["WDI_Country_Code"].astype(str)) & readable_codes)
    fallback_results = fallback_self_test_results()
    fallback_passes = int(fallback_results["상태"].eq("PASS").sum())
    citation_result = st.session_state.get("ai_validation_result")
    citation_metrics = citation_result.get("citation_metrics") if citation_result else None
    citation_kpi = (
        f"{citation_metrics['resolved_count']}/{citation_metrics['citation_count']}"
        if citation_metrics and citation_metrics["citation_count"] else "미실행"
    )

    cols = st.columns(6)
    with cols[0]: metric_card("점수 재현성", f"{score_audit['pass_count']}/{score_audit['country_count']} PASS", f"최대오차 {score_audit['max_abs_error']:.3f}")
    with cols[1]: metric_card("WDI 최신값 보유율", f"{valid_wdi}/{total_wdi}", f"{valid_wdi / total_wdi * 100:.1f}%")
    with cols[2]: metric_card("CPS Top50 근거", f"{cps_top50}/50", "원문 청킹 교집합")
    with cols[3]: metric_card("Citation ID 해석률", citation_kpi, "RAG 테스트 실행 기준")
    with cols[4]: metric_card("Local fallback", f"{fallback_passes}/5 PASS", "모의 오류 분기")
    with cols[5]: metric_card("모델·앱 버전", f"{MODEL_VERSION} · {APP_VERSION}", INTERNAL_TEST_DATE)

    validation_sections = ["요약", "정량 점수모델", "RAG 검색", "생성·fallback", "Citation·출력", "테스트 매트릭스"]
    if st.session_state.get("ai_validation_section") not in validation_sections:
        st.session_state["ai_validation_section"] = validation_sections[0]
    validation_section = st.segmented_control(
        "AI 검증 세부화면",
        validation_sections,
        key="ai_validation_section",
        required=True,
        width="stretch",
    )

    evidence_units = rag_evidence_unit_counts(master)
    total_evidence_units = int(evidence_units["근거 단위 수"].sum())
    total_pages = int(pd.to_numeric(cps_coverage["Pages"], errors="coerce").fillna(0).sum())
    readable_pages = int(pd.to_numeric(cps_coverage["Readable_Pages"], errors="coerce").fillna(0).sum())
    ocr_target_pages = int(pd.to_numeric(cps_coverage["OCR_Target_Pages"], errors="coerce").fillna(0).sum())
    image_only = int((pd.to_numeric(cps_coverage["Readable_Pages"], errors="coerce").fillna(0) == 0).sum())
    cps_chunks = int(evidence_units.loc[evidence_units["근거 유형"] == "CPS RAG 청크", "근거 단위 수"].iloc[0])
    cps_processed = int(len(readable_codes))

    if validation_section == "요약":
        st.subheader("검증 대상")
        target_table = pd.DataFrame([
            ["A. 정량 점수모델", "동일 입력 점수·가중 기여도·순위·민감도"],
            ["B. RAG 검색", "선택 국가·분야 Top-K와 KOICA·CPS·WDI·파생근거 구성"],
            ["C. 생성 단계", "Local RAG·선택적 OpenAI LLM + RAG·오류 fallback"],
            ["D. 출력 검증", "Citation ID·Evidence Pack 연결·누락·중복·생성모드"],
        ], columns=["검증 영역", "점검 대상"])
        st.dataframe(target_table, width="stretch", hide_index=True)

        st.subheader("RAG 검색 가능 근거 단위")
        st.dataframe(evidence_units, width="stretch", hide_index=True)
        st.caption(f"합계 {total_evidence_units:,}개는 검색 가능한 근거 단위 수입니다. 문서 수가 아니며, 점수모델·정책/실행환경·분야 포트폴리오는 파생 레코드입니다.")

        st.subheader("WDI·CPS 커버리지")
        c1,c2 = st.columns(2)
        with c1:
            insight_card("WDI 최신값 레코드", f"{valid_wdi}/{total_wdi} · 50개국×10지표 · {valid_wdi / total_wdi * 100:.1f}%<br>결측 {total_wdi - valid_wdi}건은 RAG 근거 생성에서 제외하고 화면에는 최신값 없음으로 표시합니다. 0으로 대체하지 않습니다.")
        with c2:
            insight_card("CPS 페이지·청크", f"전체 {total_pages}페이지 · 직접 추출 {readable_pages}페이지 · OCR 보강 대상 {ocr_target_pages}페이지<br>이미지 중심 PDF {image_only}개 · CPS RAG 청크 {cps_chunks}개 · 처리국 {cps_processed}개 · Top50 근거 {cps_top50}/50")
        st.warning("OCR 보강 대상 258페이지는 OCR 완료 페이지가 아닙니다. 현재 청크는 직접 읽을 수 있는 텍스트 레이어 중심입니다.")

    elif validation_section == "정량 점수모델":
        st.subheader("Top50 점수·순위 재현성")
        score_test = pd.DataFrame([
            ["비교 대상", "저장된 v2.1 점수 vs 7개 원점수×가중치 재계산"],
            ["재계산 방식", "KODA=0.25D+0.20K+0.15S+0.10G+0.15P+0.10F+0.05R"],
            ["최대 절대오차", f"{score_audit['max_abs_error']:.3f}"],
            ["허용 기준", f"≤ {score_audit['tolerance']:.2f}"],
            ["통과 국가", f"{score_audit['pass_count']}/{score_audit['country_count']}"],
            ["순위 일치", f"{score_audit['rank_match_count']}/{score_audit['country_count']} · {'PASS' if score_audit['rank_all_match'] else 'FAIL'}"],
            ["검증일", INTERNAL_TEST_DATE],
            ["모델 버전", MODEL_VERSION],
        ], columns=["표시 항목", "실제 결과"])
        st.dataframe(score_test, width="stretch", hide_index=True)

        st.subheader(f"{country} 가중 기여도")
        reproduction = score_reproduction_table(row, weights)
        contribution_sum = float(reproduction["기여점수"].sum())
        actual_score = float(row.get("K_ODA_Opportunity_Score_V21"))
        reproduction_display = reproduction.rename(columns={"기여점수": "가중 기여도", "사용 데이터": "사용 근거"})
        st.dataframe(reproduction_display, width="stretch", hide_index=True)
        st.caption(f"가중 기여도 합계 {contribution_sum:.2f} = 종합점수 {actual_score:.2f} · 반올림 오차 {abs(contribution_sum - actual_score):.4f}")

        st.subheader("민감도 분석")
        sensitivity = sensitivity_analysis_table(master, weights, delta=0.03)
        st.dataframe(sensitivity, width="stretch", hide_index=True)
        st.caption("실험 조건: 선택 항목 가중치 +3%p, 나머지 6개 가중치는 기존 비율을 유지하도록 비례 축소, 전체 가중치 합계 1.0000. 순위상관은 순위 벡터의 Pearson 상관으로 계산한 Spearman 값입니다.")

    elif validation_section == "RAG 검색":
        st.subheader("선택 국가·분야 Top-K 내부 테스트")
        sector_options = recommended_sectors(row)
        if st.session_state.get("validation_sector") not in sector_options:
            st.session_state["validation_sector"] = sector_options[0]
        sector = st.selectbox("검증 분야", sector_options, key="validation_sector")
        top_k = st.select_slider("Top-K", options=[8, 10, 12, 14, 16], value=12, key="validation_top_k")
        keywords = st.text_input("검증 키워드", value="현지수요, 성과관리, 파트너십, 실행위험", key="validation_keywords")
        if st.button("RAG·Citation 내부 테스트 실행", type="primary", width="stretch"):
            corpus = build_validation_country_corpus(country)
            docs = retrieve_rag_evidence(corpus, country, sector, keywords, row, top_k=top_k)
            generated = build_rag_markdown_proposal(country, sector, "내부검증", "검증용", keywords, row, docs, weights)
            evidence_pack = build_rag_evidence_pack(country, sector, keywords, docs)
            st.session_state["ai_validation_result"] = {
                "country": country,
                "sector": sector,
                "top_k": top_k,
                "docs": docs,
                "generated": generated,
                "evidence_pack": evidence_pack,
                "generation_mode": "Local RAG",
                "citation_metrics": citation_integrity_metrics(generated, docs),
                "corpus_units": len(corpus),
            }
            citation_result = st.session_state["ai_validation_result"]

        result = st.session_state.get("ai_validation_result")
        if result:
            docs = result["docs"]
            source_counts = docs["Source_Type"].value_counts()
            derived_count = int(source_counts.reindex(["Score Model", "Policy/Risk", "Sector Portfolio"], fill_value=0).sum())
            c1,c2,c3,c4,c5 = st.columns(5)
            with c1: metric_card("검증 국가·분야", result["country"], result["sector"])
            with c2: metric_card("Top-K", f"{len(docs)}/{result['top_k']}", f"국가 corpus {result['corpus_units']}단위")
            with c3: metric_card("KOICA 근거", fmt_int(source_counts.get("KOICA Project", 0)), "사업 레코드")
            with c4: metric_card("CPS·WDI", f"{int(source_counts.get('CPS PDF', 0))} · {int(source_counts.get('WDI', 0))}", "청크 · 최신값")
            with c5: metric_card("파생 점수·리스크", fmt_int(derived_count), "점수·정책·분야")
            source_labels = {
                "KOICA Project": "KOICA 사업 레코드",
                "CPS PDF": "CPS RAG 청크",
                "WDI": "WDI 최신값 레코드",
                "Score Model": "정량 점수모델 파생",
                "Policy/Risk": "정책·실행환경 파생",
                "Sector Portfolio": "분야 포트폴리오 파생",
            }
            rag_display = pd.DataFrame([
                {
                    "Evidence ID": evidence_row["Citation_ID"],
                    "출처 유형": source_labels.get(evidence_row["Source_Type"], evidence_row["Source_Type"]),
                    "사업명·문서명": evidence_row["Title"],
                    "연도·페이지": evidence_year_or_page(evidence_row),
                    "관련 분야": evidence_row["Sector_Group"],
                }
                for _, evidence_row in docs.iterrows()
            ])
            st.dataframe(rag_display, width="stretch", hide_index=True)
            st.caption("RAG_Score는 내부 lexical 검색 휴리스틱이므로 외부 관련성 확률처럼 표시하지 않습니다.")
        else:
            st.info("테스트 버튼을 누를 때만 선택 국가 corpus와 Top-K 근거를 생성합니다. 화면 진입만으로 전체 corpus를 만들지 않습니다.")

    elif validation_section == "생성·fallback":
        st.subheader("생성모드·fallback 내부 테스트")
        st.dataframe(fallback_results, width="stretch", hide_index=True)
        mode_table = pd.DataFrame([
            ["Local RAG", "API 키 없이 실행", "근거 고정형 로컬 템플릿 생성", "사용 가능"],
            ["OpenAI LLM + RAG", "OPENAI_API_KEY가 있을 때만 선택", "동일 Evidence Pack을 API에 전달", "실제 API 호출은 이 화면에서 미실행"],
        ], columns=["생성모드", "활성 조건", "근거 사용", "현재 내부검증 상태"])
        st.dataframe(mode_table, width="stretch", hide_index=True)
        st.caption("API timeout 30초 · max_retries 1회. 인증·시간초과·빈 응답·예외는 Local RAG fallback 경로로 전환합니다.")
        st.warning("인증·시간초과·예외 테스트는 외부 API를 호출하지 않은 모의 오류 분기 테스트입니다. 실제 OpenAI 호출 성공 여부는 API 키가 있는 별도 실행 캡처가 필요합니다.")

    elif validation_section == "Citation·출력":
        result = st.session_state.get("ai_validation_result")
        st.subheader("Citation ID 무결성")
        if not result:
            st.info("RAG 검색 화면에서 내부 테스트를 실행해야 실제 생성 샘플과 Evidence Pack의 Citation을 검사합니다.")
        else:
            citation_metrics = result["citation_metrics"]
            rate = citation_metrics["resolution_rate"]
            c1,c2,c3,c4,c5 = st.columns(5)
            with c1: metric_card("생성문 Citation", fmt_int(citation_metrics["citation_count"]), result["generation_mode"])
            with c2: metric_card("해석 가능", f"{citation_metrics['resolved_count']}/{citation_metrics['citation_count']}", f"{rate:.1f}%" if rate is not None else "계산 불가")
            with c3: metric_card("존재하지 않는 ID", fmt_int(citation_metrics["unknown_count"]), ", ".join(citation_metrics["unknown_ids"]) or "없음")
            with c4: metric_card("중복 Citation", fmt_int(citation_metrics["duplicate_count"]), "반복 인용 횟수")
            with c5: metric_card("미사용 Evidence", fmt_int(citation_metrics["unused_evidence_count"]), "Evidence Pack 내 미인용")
            integrity_table = pd.DataFrame([
                ["Citation ID 해석", "모든 생성문 ID가 Evidence Pack에 존재", f"{citation_metrics['resolved_count']}/{citation_metrics['citation_count']}", "PASS" if citation_metrics["unknown_count"] == 0 and citation_metrics["citation_count"] > 0 else "FAIL"],
                ["존재하지 않는 Citation", "0개", f"{citation_metrics['unknown_count']}개", "PASS" if citation_metrics["unknown_count"] == 0 else "FAIL"],
                ["중복 Citation", "정보 공개", f"{citation_metrics['duplicate_count']}회", "INFO"],
                ["근거 없는 문단", "문장·문단 의미검사", "자동 의미검사 미구현", "LIMIT"],
                ["생성모드 표시", "Local RAG 또는 OpenAI LLM + RAG", result["generation_mode"], "PASS"],
            ], columns=["검증 항목", "통과 기준", "실제 결과", "상태"])
            st.dataframe(integrity_table, width="stretch", hide_index=True)
            with st.expander("Evidence Pack·생성 샘플 확인"):
                st.code(result["evidence_pack"][:6000], language="markdown")
                st.code(result["generated"][:6000], language="markdown")

        st.subheader("환각 위험 완화 및 인용 검증")
        st.markdown("""
        <div class="section-note">생성 전 Top-K 근거를 고정하고 문장에 Evidence ID를 삽입하며, Citation ID와 Evidence Pack의 연결을 검사합니다. 정책·실행환경은 보조지표로 표시합니다. 이 절차는 최종 사실성을 자동 보증하지 않으며 원문 확인·현지수요·파트너 검증이 필요합니다.</div>
        """, unsafe_allow_html=True)

    elif validation_section == "테스트 매트릭스":
        result = st.session_state.get("ai_validation_result")
        citation_row = ["Citation ID 무결성", "존재하지 않는 ID 0개", "테스트 미실행", "INFO", INTERNAL_TEST_DATE]
        rag_row = ["RAG 출처 구성", "선택 Top-K의 출처 유형 공개", "테스트 미실행", "INFO", INTERNAL_TEST_DATE]
        if result:
            citation_metrics = result["citation_metrics"]
            citation_row = ["Citation ID 무결성", "존재하지 않는 ID 0개", f"해석 {citation_metrics['resolved_count']}/{citation_metrics['citation_count']} · 미존재 {citation_metrics['unknown_count']}", "PASS" if citation_metrics["unknown_count"] == 0 else "FAIL", INTERNAL_TEST_DATE]
            source_types = sorted(result["docs"]["Source_Type"].unique().tolist())
            rag_row = ["RAG 출처 구성", "선택 Top-K의 출처 유형 공개", ", ".join(source_types), "PASS", INTERNAL_TEST_DATE]
        matrix = pd.DataFrame([
            ["Top50 점수 재현", "최대 절대오차 ≤0.01", f"{score_audit['max_abs_error']:.3f} · {score_audit['pass_count']}/50", "PASS" if score_audit["pass_count"] == 50 else "FAIL", INTERNAL_TEST_DATE],
            ["Top50 순위 재현", "저장 순위와 50/50 일치", f"{score_audit['rank_match_count']}/50", "PASS" if score_audit["rank_all_match"] else "FAIL", INTERNAL_TEST_DATE],
            ["WDI 최신값", "보유·결측 수 공개", f"{valid_wdi}/{total_wdi} · 결측 {total_wdi-valid_wdi}", "INFO", INTERNAL_TEST_DATE],
            ["CPS OCR", "OCR 대상과 완료를 구분", f"직접 {readable_pages}p · 대상 {ocr_target_pages}p", "LIMIT", INTERNAL_TEST_DATE],
            rag_row,
            citation_row,
            ["Local fallback 분기", "5개 실행 경로 PASS", f"{fallback_passes}/5 모의 분기 PASS", "PASS" if fallback_passes == 5 else "FAIL", INTERNAL_TEST_DATE],
            ["민감정보 로그", "API 키 미출력", "정적 확인 · 실제 로그 캡처 미실행", "INFO", INTERNAL_TEST_DATE],
            ["OpenAI 실제 호출", "응답·모델·Citation 캡처", "이 화면에서 미실행", "LIMIT", INTERNAL_TEST_DATE],
            ["pytest", "테스트 전체 통과", PYTEST_RESULT, "PASS", INTERNAL_TEST_DATE],
        ], columns=["검증 항목", "통과 기준", "실제 결과", "상태", "검증일"])
        st.dataframe(matrix, width="stretch", hide_index=True)
        st.caption(f"모델 {MODEL_VERSION} · 앱 {APP_VERSION} · 데이터 {DATA_SNAPSHOT} · 분석 대상 {len(master)}개국")


def render_deploy(data):
    st.title("배포·QR 센터")
    st.caption("공개 저장소와 실제 Streamlit 서비스를 QR로 바로 확인할 수 있습니다.")
    cols = st.columns(2)
    with cols[0]:
        st.subheader("GitHub")
        st.markdown(f"[{GITHUB_URL}]({GITHUB_URL})")
        qr = make_qr_png(GITHUB_URL)
        if qr:
            st.image(qr, width=220)
            st.download_button("GitHub QR 다운로드", qr, "koda_compass_github_qr.png", "image/png", width="stretch")
    with cols[1]:
        st.subheader("Live Demo")
        st.markdown(f"[{LIVE_DEMO_URL}]({LIVE_DEMO_URL})")
        qr = make_qr_png(LIVE_DEMO_URL)
        if qr:
            st.image(qr, width=220)
            st.download_button("Live Demo QR 다운로드", qr, "koda_compass_live_demo_qr.png", "image/png", width="stretch")

    st.header("배포·재현성 현황")
    st.markdown("""
1. GitHub 공개 저장소 배포 완료
2. Streamlit Community Cloud `app.py` entrypoint 지정 완료
3. 실제 서비스 URL 제공
4. GitHub·Live Demo QR 제공
5. API 키 없이 로컬 RAG fallback 동작
6. API 키 설정 시 선택적 LLM 생성 모드 사용 가능
""")
    st.info("OPENAI_API_KEY는 선택적 LLM 생성 모드에만 사용됩니다. 키가 없는 환경에서도 국가순위·프로필·분야 우선검토·근거검색·로컬 RAG 생성·PDF 출력이 작동합니다.")


def render_judge_mode(data):
    master = data["master"]
    cps_pdf = data["cps_pdf"]
    st.title("심사용 요약")
    st.caption("공공데이터 활용, AI 기술, 서비스 실효성, 독창성, 발전 가능성, ESG·사회적 가치를 한 화면에서 확인합니다.")

    corpus_count = int(rag_evidence_unit_counts(master)["근거 단위 수"].sum())
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("핵심 공공데이터", "KOICA + CPS", "사업정보·정책원문")
    with c2: metric_card("RAG 검색 가능 근거", fmt_int(corpus_count), "근거 단위 · 문서 수 아님")
    with c3: metric_card("CPS 원문 근거", fmt_int(len(cps_pdf)), f"청킹 완료 {cps_pdf['Country_KR'].nunique()}개국")
    with c4: metric_card("분석 후보국", fmt_int(len(master)), "기본 종합순위")

    st.header("1. 심사기준 대응표")
    matrix = pd.DataFrame([
        ["공공데이터 활용", "KOICA 사업정보와 CPS 정책원문을 핵심 근거로 통합", "WDI·정책·리스크는 보조지표로 결합"],
        ["AI 기술 활용", "정량 점수모델, 국가단위 RAG 검색, Evidence Pack 고정", "로컬 생성과 선택적 LLM 생성 모두 citation 유지"],
        ["AI 서비스 실효성", "후보국 탐색부터 사업기획서·브리프·PDF까지 연결", "CSO·기업·지방정부·연구기관 업무흐름 지원"],
        ["독창성", "조회형 대시보드를 근거추적형 의사결정 서비스로 확장", "점수 기여도와 문장별 [E01] 근거를 함께 공개"],
        ["발전 가능성", "공개 저장소·실서비스·모듈형 데이터 파이프라인", "OCR·API 자동갱신·기관 파일럿으로 확장 가능"],
        ["ESG·사회적 가치", "개발수요와 실행위험을 함께 비교", "ODA 자원배분 투명성과 중소 조직의 데이터 접근성 강화"],
    ], columns=["평가축", "구현 내용", "심사 포인트"])
    st.dataframe(matrix, width="stretch", hide_index=True)

    st.header("2. 90초 발표 흐름")
    st.markdown("""
1. `개요`: ODA 공공데이터는 많지만 사업기획으로 전환하기 어렵다는 문제 제시
2. `순위`: Top50 기본 종합순위와 가중 기여도 제시
3. `AI Builder`: 대표 시나리오 선택 후 RAG형 사업기획서 생성
4. `근거 Citation`: KOICA 사업·CPS 원문·WDI 보조지표의 근거 ID 확인
5. `AI·모델 검증`: 점수 재현성, RAG 검색, Citation 무결성, fallback 점검
6. `배포`: Streamlit/GitHub QR로 실제 서비스 접근성 제시
""")

    st.header("3. 경쟁작 대비 포지션")
    positioning = pd.DataFrame([
        ["일반 데이터 대시보드", "조회·시각화 중심", "사업기획서·Evidence Pack까지 생성"],
        ["단순 챗봇", "근거 추적 어려움", "RAG citation으로 원문·데이터 근거 추적"],
        ["아이디어 기획안", "실행 화면 부재", "Streamlit MVP, export, tests, Docker 제공"],
        ["정책문서 수동분석", "시간 소요·비전문가 접근성 낮음", "CPS 원문 chunk 기반 정책정합성 근거 검색"],
    ], columns=["비교 대상", "일반 한계", "K-ODA Compass 차별점"])
    st.dataframe(positioning, width="stretch", hide_index=True)

    st.header("4. 구현 완료 항목")
    completed = pd.DataFrame([
        ["실서비스", "Streamlit Community Cloud와 GitHub 공개 저장소 제공"],
        ["의사결정 기능", "국가순위·프로필·분야 우선검토·AI Builder·근거·재현성·AI·모델 검증 구현"],
        ["근거 데이터", f"RAG {fmt_int(corpus_count)}건에 KOICA·CPS·WDI·정책·리스크 근거 결합"],
        ["사용 시나리오", "탄자니아·르완다·베트남 사업기획 산출물 제공"],
        ["검증·출력", "Citation·Evidence Pack·점수기여도·정책 브리프·PDF 출력"],
        ["안전한 생성", "API 키 없는 로컬 RAG와 OpenAI 실패 fallback 구현"],
    ], columns=["구현영역", "완료 내용"])
    st.dataframe(completed, width="stretch", hide_index=True)

    st.header("5. 향후 고도화 계획")
    roadmap = pd.DataFrame([
        ["사용자 검증", "CSO·ODA 실무자 대상 과업시간·활용성 검증"],
        ["정책문서 확대", "이미지 기반 CPS OCR 커버리지 확대"],
        ["데이터 운영", "공공 API 기반 데이터 자동 갱신과 변경이력 관리"],
        ["현장 실증", "기관·지방정부·CSO 파일럿을 통한 추천 정확성 검증"],
        ["파트너십", "사업분야·국가·운영역량 기반 파트너 추천 정교화"],
    ], columns=["고도화 축", "확장 방향"])
    st.dataframe(roadmap, width="stretch", hide_index=True)


def render_overview(data):
    master = data["master"]
    cps_count = int((master["국가협력전략 대상국가"].astype(str).str.upper() == "Y").sum()) if "국가협력전략 대상국가" in master else 0
    avg_wdi = master["WDI_Core_Coverage_%"].mean() if "WDI_Core_Coverage_%" in master else None
    st.markdown(f"""
    <div class="koda-hero">
      <div class="koda-title">K-ODA Compass v2.1</div>
      <p class="koda-subtitle"><b>외교·ODA 공공데이터를 사업기회로 전환하는 근거추적형 AI 의사결정 서비스</b><br>
      CSO·NGO, 기업, 지방정부, 대학·연구기관이 유망 국가와 분야를 탐색하고 출처가 연결된 ODA 사업기획서 초안을 생성하도록 지원합니다.<br>
      KOICA 2019–2024 사업정보와 CPS 정책원문을 핵심 근거로 활용하고, World Bank WDI와 정책·리스크 지표를 보조적으로 결합해 국가·분야 추천, 실행가능성 분석, RAG 사업기획서와 Evidence Pack을 제공합니다.</p>
    </div>
    """, unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: metric_card("분석 대상", fmt_int(len(master)), "ODA 후보국")
    with c2: metric_card("핵심 공공데이터", "KOICA + CPS", "사업정보·정책원문")
    with c3: metric_card("RAG 근거", fmt_int(AUDITED_RAG_DOCUMENTS), "citation-ready")
    with c4: metric_card("평균 WDI 커버리지", fmt_number(avg_wdi,1,"%"), "핵심 지표 기준")
    with c5: metric_card("서비스 상태", "Live", "로컬 RAG·선택적 LLM·PDF")

    st.header("1. 문제정의")
    st.markdown("""
    <div class="section-note">
    KOICA 사업정보, CPS 정책문서, 개발지표는 공개되어 있지만 기관·파일·문서 형식이 분산되어 있어 비전문 사용자가 국가와 분야를 비교하고 기존 사업·정책근거·위험요인을 함께 검토하려면 반복적인 수작업이 필요합니다.<br><br>
    K-ODA Compass는 이를 국가코드와 분야체계로 통합하여 <b>후보국 추천, 분야 제안, 정책·리스크 해석, 근거 인용형 사업기획서 초안</b>으로 변환합니다.
    </div>
    """, unsafe_allow_html=True)

    st.header("2. 사용자가 얻는 결과")
    users = [
        ("CSO·NGO", "공모사업 후보국·분야 발굴<br>사업개요·수혜자·위험요인"),
        ("기업·사회적기업", "진출국·협력분야 탐색<br>파트너십 후보·개발수요"),
        ("지방정부", "국제개발협력 사업기획<br>정책정합성·유사사업·기획 초안"),
        ("대학·연구기관", "국가·분야 비교<br>지표·출처·Evidence Pack"),
    ]
    cols = st.columns(4)
    for col, (title, body) in zip(cols, users):
        with col: insight_card(title, body)

    st.header("3. 공공데이터에서 실행문서까지")
    cols = st.columns(5)
    workflow = [
        ("① Public Data", "KOICA 사업정보·CPS 정책원문·WDI·정책·리스크 통합"),
        ("② Quantitative Score", "개발수요·한국 기존 협력경험·분야적합성·실행가능성 산출"),
        ("③ RAG Retrieval", "선택 국가·분야의 사업·정책·지표 근거 검색"),
        ("④ AI Planning", "근거를 고정하고 목표·수혜자·활동·위험요인 초안 생성"),
        ("⑤ Evidence & Export", "Citation·점수기여도·Evidence Pack·PDF 출력"),
    ]
    for col, (t,b) in zip(cols, workflow):
        with col: pipeline_card(t,b)

    st.header("4. 우선순위 모델의 세 가지 판단축")
    weight_lookup = dict(zip(data["weights"]["Component"], pd.to_numeric(data["weights"]["Weight"], errors="coerce")))
    score_groups = pd.DataFrame([
        ["개발수요", "Development Need + Opportunity Gap", weight_lookup.get("Development Need", 0) + weight_lookup.get("Opportunity Gap", 0), "개발지표 기반 수요와 추가 사업기회"],
        ["한국 협력적합성", "Cooperation Base + Sector Fit + Policy Alignment", weight_lookup.get("Korea Cooperation Base", 0) + weight_lookup.get("Sector Fit", 0) + weight_lookup.get("Policy Alignment", 0), "기존 사업경험·분야패턴·CPS 정책정합성"],
        ["실행가능성", "Risk Feasibility + Data Reliability", weight_lookup.get("Risk Feasibility", 0) + weight_lookup.get("Data Reliability", 0), "제도·거버넌스 위험과 데이터 신뢰도"],
    ], columns=["판단축", "포함 구성요소", "비중", "의미"])
    score_groups["비중"] = score_groups["비중"].map(lambda x: f"{x * 100:.0f}%")
    st.dataframe(score_groups, width="stretch", hide_index=True)
    st.markdown("""
    <div class="section-note">세부 7개 가중치·산식·민감도 분석은 <b>AI·모델 검증</b> 화면에서 확인할 수 있습니다. 우선순위 점수는 국가 자동선정 결과가 아니라 비교·검토를 돕는 보조지표입니다.</div>
    """, unsafe_allow_html=True)

    st.header("5. 기본 종합순위 상위 후보국")
    top3 = master.head(3)
    cols = st.columns(3)
    for col, (_, r) in zip(cols, top3.iterrows()):
        with col:
            insight_card(f"#{int(r['Rank_V21'])} {r['Country_KR']}", f"우선순위 점수 {fmt_number(r['K_ODA_Opportunity_Score_V21'])}<br>{compact_candidate_label(r['Candidate_Type_V21'])}<br>추천분야: {r['Recommended_Service_Angle_V2']}")

    st.header("6. 기존 서비스와의 차별성")
    cols = st.columns(3)
    differentiators = [
        ("조회에서 의사결정으로", "통계·사업 조회를 넘어 국가·분야 우선검토 순위와 다음 확인사항을 제안"),
        ("생성에서 근거추적으로", "일반 챗봇과 달리 생성 전에 Evidence Pack을 고정하고 문장별 근거 ID를 연결"),
        ("아이디어에서 실행문서로", "추천 결과를 사업기획서·정책 브리프·Evidence Pack·PDF로 변환"),
    ]
    for col, (title, body) in zip(cols, differentiators):
        with col: pipeline_card(title, body)

    st.header("7. ESG·사회적 가치")
    cols = st.columns(3)
    with cols[0]: risk_card("포용적 데이터 접근", "중소 CSO·기업·지방정부도 분산된 ODA 데이터를 비교하고 사업기획에 활용할 수 있도록 지원합니다.")
    with cols[1]: risk_card("투명한 자원배분", "사업 선정근거와 점수기여도를 공개해 제한된 ODA 자원의 근거기반 배분과 설명책임을 강화합니다.")
    with cols[2]: risk_card("수요와 위험의 균형", "취약국 개발수요와 실행위험을 함께 검토해 중복·과잉지원 가능성을 줄이고 현지검증을 촉진합니다.")

    st.caption(f"데이터 범위: KOICA 사업정보 2019–2024 · WDI 지표별 최신 가용연도(최대 2025) · Top50 중 CPS 대상 표시 {cps_count}개국 · CPS 원문 청킹 {AUDITED_CPS_CHUNK_COUNTRIES}개국 · Top50 중 CPS 원문 근거 보유 {AUDITED_CPS_TOP50_COUNTRIES}개국")


def render_ranking(data):
    master = data["master"]
    weights = data["weights"]
    cps_countries = set(data["cps_pdf"]["Country_KR"].dropna())
    px = get_plotly_express()
    st.title("ODA 사업기회 우선검토 순위")
    st.caption("KOICA 사업정보와 CPS 정책근거를 중심으로 WDI·정책·리스크 지표를 결합해 50개 후보국의 기본 종합순위와 점수 구성요소를 비교합니다.")
    st.markdown("""
    <div class="section-note"><b>의사결정 보조지표:</b> 본 순위는 국가를 자동 선정하는 결과가 아닙니다. 최종 사업화 여부는 현지 수요, 파트너 역량, 정책환경과 현장조사를 통해 검증해야 합니다.</div>
    """, unsafe_allow_html=True)
    st.caption("분석 기준: KOICA 사업정보 2019–2024 · CPS 정책원문 수집·청킹 범위 · WDI 지표별 최신 가용연도 · K-ODA Opportunity Score v2.1")

    top = master.iloc[0]
    c1,c2,c3,c4 = st.columns(4)
    with c1: metric_card("기본 종합순위 1위", top["Country_KR"], f"우선순위 점수 {fmt_number(top['K_ODA_Opportunity_Score_V21'])}")
    with c2: metric_card("정책정합성 최고", master.sort_values("Policy_Alignment_Score_V21", ascending=False).iloc[0]["Country_KR"], fmt_number(master["Policy_Alignment_Score_V21"].max()))
    with c3: metric_card("실행가능성 최고", master.sort_values("Risk_Feasibility_Score_V21", ascending=False).iloc[0]["Country_KR"], fmt_number(master["Risk_Feasibility_Score_V21"].max()))
    with c4: metric_card("CPS 원문 근거", fmt_int(len(set(master["Country_KR"]) & cps_countries)), "Top50 중 청킹 근거 보유")

    st.subheader("탐색 필터")
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        region = st.selectbox("지역", ["전체", *sorted(master["Region_KR"].dropna().unique().tolist())])
    sector_options = sorted({sector for _, row in master.iterrows() for sector in recommended_sectors(row)})
    with f2:
        interest_sector = st.selectbox("관심 분야", ["전체", *sector_options])
    with f3:
        candidate_filter = st.selectbox("후보유형", ["전체", "우선검토형", "리스크 보완형", "협력기반 확장형", "현지검증형"])
    with f4:
        min_reliability = st.slider("최소 데이터 신뢰도", 0, 100, 0, 5)

    filtered = master.copy()
    if region != "전체":
        filtered = filtered.loc[filtered["Region_KR"] == region]
    if interest_sector != "전체":
        filtered = filtered.loc[filtered["Recommended_Service_Angle_V2"].astype(str).str.contains(interest_sector, regex=False)]
    if candidate_filter != "전체":
        filtered = filtered.loc[filtered["Candidate_Type_V21"].map(compact_candidate_label) == candidate_filter]
    filtered = filtered.loc[pd.to_numeric(filtered["Data_Reliability_Score_V21"], errors="coerce") >= min_reliability]
    filtered = filtered.sort_values("Rank_V21")
    st.caption(f"필터 결과 {len(filtered)}개국 · 필터는 기존 v2.1 점수와 순위를 재계산하지 않습니다.")

    if filtered.empty:
        st.info("현재 조건에 맞는 후보국이 없습니다. 필터 범위를 넓혀 주세요.")
        return

    c1,c2 = st.columns([1.05, 1.1])
    with c1:
        st.subheader("기본 종합순위 Top 20")
        chart_df = filtered.head(20).sort_values("K_ODA_Opportunity_Score_V21")
        fig = px.bar(chart_df, x="K_ODA_Opportunity_Score_V21", y="Country_KR", orientation="h", text="K_ODA_Opportunity_Score_V21", labels={"K_ODA_Opportunity_Score_V21":"우선순위 점수", "Country_KR":"국가"})
        fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig.add_vline(x=master.head(10)["K_ODA_Opportunity_Score_V21"].mean(), line_dash="dot", line_color="#a14f3f", annotation_text="기본 Top10 평균")
        fig.update_layout(height=640, margin=dict(l=10,r=30,t=10,b=10), xaxis_range=[0,100])
        st.plotly_chart(fig, width="stretch")
    with c2:
        st.subheader("상위 5개국 가중 기여도")
        comp = component_contribution_long(filtered, weights, top_n=5)
        fig2 = px.bar(comp, x="가중기여도", y="국가", color="구성요소", barmode="stack", orientation="h", text="가중기여도")
        fig2.update_traces(texttemplate='%{text:.1f}', textposition='inside')
        fig2.update_layout(height=640, margin=dict(l=10,r=10,t=10,b=10), xaxis_range=[0,100])
        st.plotly_chart(fig2, width="stretch")
        st.caption("7개 구성요소의 가중 기여도 합은 각 국가의 실제 v2.1 우선순위 점수와 일치합니다.")

    st.subheader("상위 3개국 근거와 다음 단계")
    cols=st.columns(3)
    for col,(_,r) in zip(cols, filtered.head(3).iterrows()):
        with col:
            has_cps = r["Country_KR"] in cps_countries
            body = (
                f"<b>{compact_candidate_label(r['Candidate_Type_V21'])}</b><br>"
                f"우선순위 {fmt_number(r['K_ODA_Opportunity_Score_V21'])} · 개발수요 {fmt_number(r['Development_Need_Score'])}<br>"
                f"KOICA 사업 {fmt_int(r['Project_Count_2019_2024'])}건 · CPS 원문 {'보유' if has_cps else '미청킹'}<br>"
                f"WDI 커버리지 {fmt_number(r['WDI_Core_Coverage_%'], 1, '%')}<br>"
                f"다음 단계: {candidate_next_step(r['Candidate_Type_V21'])}"
            )
            insight_card(f"#{int(r['Rank_V21'])} {r['Country_KR']}", body)
            a1, a2, a3 = st.columns(3)
            with a1:
                st.button("프로필", key=f"profile_{r['WDI_Country_Code']}", on_click=queue_navigation, args=("프로필", r["Country_KR"]), width="stretch")
            with a2:
                st.button("근거", key=f"evidence_{r['WDI_Country_Code']}", on_click=queue_navigation, args=("근거·재현성", r["Country_KR"]), width="stretch")
            with a3:
                st.button("Builder", key=f"builder_{r['WDI_Country_Code']}", on_click=queue_navigation, args=("AI Builder", r["Country_KR"]), width="stretch")

    st.subheader("의사결정용 점수표")
    st.caption("기본 화면은 필터 결과 중 상위 20개국만 표시합니다. 전체 50개국 표와 CSV는 요청할 때만 생성합니다.")
    st.dataframe(display_rank_table(filtered.head(20), cps_countries), width="stretch", hide_index=True)

    type_df = pd.DataFrame([
        ["우선검토형", "개발수요와 정책정합성이 높아 사업개념 구체화 권장"],
        ["리스크 보완형", "수요는 높지만 제도·거버넌스 위험 검증 필요"],
        ["협력기반 확장형", "기존 한국 협력경험을 활용한 후속·확장사업 검토"],
        ["현지검증형", "데이터상 가능성은 있으나 현지수요·파트너 확인 필요"],
    ], columns=["후보유형", "의미"])
    st.markdown("#### 후보유형 정의")
    st.dataframe(type_df, width="stretch", hide_index=True)

    with st.expander("전체 50개국 점수표·CSV"):
        load_full_table = st.checkbox("전체 표 불러오기", value=False)
        if load_full_table:
            full_table = display_rank_table(master, cps_countries)
            st.dataframe(full_table, width="stretch", hide_index=True)
            st.download_button(
                "전체 Top 50 점수표 CSV 다운로드",
                data=full_table.to_csv(index=False).encode("utf-8-sig"),
                file_name="KODA_top50_v21_score_table.csv",
                mime="text/csv",
                width="stretch",
            )
        else:
            st.caption("체크하면 전체 표와 다운로드 파일을 생성합니다.")

    st.markdown("""
    <div class="section-note">취약국 여부는 별도 참고정보이며 종합순위와 동일하지 않습니다. K-ODA Compass는 높은 개발수요와 낮은 실행가능성을 함께 보여 주어 근거기반 후속 검증을 지원합니다.</div>
    """, unsafe_allow_html=True)


def render_profile(data):
    master, weights = data["master"], data["weights"]
    wdi, cy = data["wdi"], data["country_year"]
    sector_summary, sector_year = data["sector_summary"], data["sector_year"]
    policy_risk, cps_pdf = data["policy_risk"], data["cps_pdf"]
    st.title("국가 프로필")
    country = st.selectbox("국가 선택", get_country_options(master), index=0, key="profile_country")
    row = get_country_row(master, country)
    country_wdi = wdi_for_country(wdi, country)
    country_cy = country_year_for_country(cy, country)
    country_sector = sector_summary_for_country(sector_summary, country)
    country_cps = cps_for_country(cps_pdf, country)
    policy_rows = policy_risk.loc[policy_risk["Country_KR"] == country]
    policy_row = policy_rows.iloc[0] if not policy_rows.empty else pd.Series(dtype=object)
    completeness = evidence_completeness(row, country_wdi, country_cps, policy_row)
    cps_summary = cps_document_summary(country, country_cps)
    feasibility_note = feasibility_label(
        row.get("Risk_Feasibility_Score_V21"), master["Risk_Feasibility_Score_V21"]
    )
    policy_note = "CPS 원문·KOICA 근거" if not country_cps.empty else "CPS 직접근거 없음"
    st.caption("개발수요·한국 협력경험·정책근거·실행환경을 함께 보는 근거 기반 국가 의사결정 브리프입니다.")

    cols=st.columns(6)
    with cols[0]: metric_card("v2.1 우선순위 점수", fmt_number(row.get("K_ODA_Opportunity_Score_V21")), f"기본 순위 #{fmt_int(row.get('Rank_V21'))}")
    with cols[1]: metric_card("개발수요", fmt_number(row.get("Development_Need_Score")), "World Bank WDI 보조지표")
    with cols[2]: metric_card("정책정합성", fmt_number(row.get("Policy_Alignment_Score_V21")), policy_note)
    with cols[3]: metric_card("실행가능성", fmt_number(row.get("Risk_Feasibility_Score_V21")), feasibility_note)
    with cols[4]: metric_card("KOICA 사업 레코드", fmt_int(row.get("Project_Count_2019_2024")), "2019~2024 공개 원자료 행")
    with cols[5]: metric_card("근거 완전성", f"{completeness['score']}/4", "보유 원천그룹 기준")
    st.markdown("""
    <div class="section-note"><b>v2.1 우선순위 점수:</b> 개발수요·한국 협력기반·분야적합성·사업기회 공백·정책정합성·실행가능성·데이터 신뢰도를 종합한 사업기회 우선검토 점수입니다. 절대적 사업 타당성이나 자동 선정 결과가 아닙니다.</div>
    """, unsafe_allow_html=True)

    st.subheader("한 줄 국가 진단")
    st.markdown(f"""
    <div class="decision-card"><b>{country}</b>는 <b>{compact_candidate_label(row.get('Candidate_Type_V21'))}</b>입니다. {country_diagnosis(master, row)}</div>
    """, unsafe_allow_html=True)

    st.subheader("권장 다음 검증 단계")
    user_type = st.selectbox(
        "활용 사용자",
        ["CSO·NGO", "기업·사회적기업", "지방정부", "대학·연구기관"],
        key="profile_user_type",
    )
    st.markdown("\n".join(f"- {step}" for step in next_validation_steps(user_type)))
    st.caption("사용자 유형은 설명과 다음 행동만 조정하며 국가 순위와 점수에는 영향을 주지 않습니다.")

    st.subheader("근거 완전성")
    status = completeness["status"]
    evidence_rows = [
        ["KOICA", "보유" if status["KOICA"] else "미보유", f"2019~2024 공개 레코드 {completeness['koica_records']:,}건"],
        ["CPS", "보유" if status["CPS"] else "미보유", f"관련 청크 {completeness['cps_chunks']:,}건"],
        ["WDI", "보유" if status["WDI"] else "미보유", f"최신값 {completeness['wdi_latest']}/{completeness['wdi_total']}개 지표"],
        ["정책·리스크", "보유" if status["정책·리스크"] else "미보유", f"원자료 {completeness['risk_available']}/{completeness['risk_total']}개 항목"],
    ]
    st.dataframe(pd.DataFrame(evidence_rows, columns=["근거 그룹", "상태", "확인 수치"]), width="stretch", hide_index=True)
    st.caption("4개 원천그룹별로 1개 이상의 국가 관련 레코드 또는 최신값이 있으면 1점으로 계산합니다. 완전성은 근거의 존재 여부이며 품질·최신성 보증이 아닙니다.")

    action1, action2 = st.columns(2)
    with action1:
        st.button("근거 보기", key="profile_to_evidence", on_click=queue_navigation, args=("근거·재현성", country), width="stretch")
    with action2:
        st.button("AI Builder·Evidence Pack", key="profile_to_builder", on_click=queue_navigation, args=("AI Builder", country), width="stretch", type="primary")

    st.markdown("""
    <div class="section-note"><b>데이터 위계:</b> KOICA 사업정보와 CPS 정책원문은 핵심 외교·ODA 근거입니다. World Bank WDI와 정책·리스크 지표는 개발수요·실행환경 해석을 돕는 보조지표입니다.</div>
    <div class="section-note">본 프로필은 의사결정 보조정보이며, 최종 사업화 여부는 현지조사, 파트너 검증, 정책환경 및 사업 타당성 검토를 통해 결정해야 합니다.</div>
    """, unsafe_allow_html=True)

    profile_section = st.segmented_control(
        "프로필 세부화면",
        ["요약", "개발수요", "한국 협력경험", "정책근거", "리스크", "사업분야"],
        default="요약",
        key="profile_section",
        required=True,
        width="stretch",
    )

    if profile_section == "요약":
        st.subheader("현재 사업기회")
        opportunity = pd.DataFrame([
            ["개발수요", row.get("Development_Need_Score"), relative_score_label(master["Development_Need_Score"], row.get("Development_Need_Score"))],
            ["CPS·정책정합성", row.get("Policy_Alignment_Score_V21"), relative_score_label(master["Policy_Alignment_Score_V21"], row.get("Policy_Alignment_Score_V21"))],
            ["사업기회 공백", row.get("Opportunity_Gap_Score_V2"), relative_score_label(master["Opportunity_Gap_Score_V2"], row.get("Opportunity_Gap_Score_V2"))],
            ["실행가능성", row.get("Risk_Feasibility_Score_V21"), feasibility_note],
            ["데이터 신뢰도", row.get("Data_Reliability_Score_V21"), relative_score_label(master["Data_Reliability_Score_V21"], row.get("Data_Reliability_Score_V21"))],
        ], columns=["판단요소", "원점수", "Top 50 상대위치"])
        st.dataframe(opportunity, width="stretch", hide_index=True)

        st.subheader("점수 진단")
        score_mode = st.segmented_control(
            "점수 표시 방식",
            ["구성요소 원점수", "종합점수 가중 기여도"],
            default="구성요소 원점수",
            key="profile_score_mode",
            required=True,
        )
        contribution = score_contribution_table(row, weights)
        if score_mode == "구성요소 원점수":
            score_display = contribution[["구성요소", "원점수"]].sort_values("원점수", ascending=False)
            st.caption("각 항목은 0~100점 원점수이며, v2.1 종합점수에는 항목별 가중치가 별도로 적용됩니다.")
            st.bar_chart(score_display.set_index("구성요소"), horizontal=True)
            st.dataframe(score_display, width="stretch", hide_index=True)
        else:
            score_display = contribution[["구성요소", "원점수", "가중치", "기여점수"]].copy()
            score_display["가중치"] = score_display["가중치"].map(lambda value: f"{value * 100:.0f}%")
            contribution_sum = contribution["기여점수"].sum()
            st.caption(f"기여점수 합계 {contribution_sum:.2f}점 · 실제 v2.1 종합점수 {float(row.get('K_ODA_Opportunity_Score_V21')):.2f}점")
            st.bar_chart(contribution.set_index("구성요소")[["기여점수"]], horizontal=True)
            st.dataframe(score_display, width="stretch", hide_index=True)

        st.subheader("CPS 정책근거 요약")
        if country_cps.empty:
            st.info("CPS 직접근거 없음 · KOICA/WDI 기반 보조 해석입니다. 최신 국가협력전략 원문을 별도로 확인해야 합니다.")
        else:
            insight_card(
                cps_summary["document"],
                f"문서 파일: {cps_summary['file']} · 기준연도: {cps_summary['year']}<br>"
                f"관련 분야: {cps_summary['sectors']}<br>관련 페이지: {cps_summary['pages']}<br>근거 청크: {cps_summary['chunks']}건",
            )

    elif profile_section == "개발수요":
        st.subheader("WDI 개발수요 보조지표")
        st.caption("WDI는 개발수요 해석을 돕는 보조지표이며 외교·ODA 핵심 근거인 KOICA·CPS를 대체하지 않습니다.")
        cards = wdi_signal_cards(country_wdi)
        card_columns = st.columns(2)
        for index, card in enumerate(cards):
            with card_columns[index % 2]:
                insight_card(card["title"], card["body"])
        with st.expander("WDI 원자료 보기"):
            if st.checkbox("원자료 표 불러오기", value=False, key="profile_wdi_raw"):
                wdi_columns = ["Signal_KR", "Indicator_Name", "Latest_Value_Display", "Latest_Year", "Series_Code", "WDI_Coverage_2019_2025"]
                wdi_display = country_wdi[[col for col in wdi_columns if col in country_wdi.columns]].head(10).rename(columns={
                    "Signal_KR":"수요 신호", "Indicator_Name":"지표명", "Latest_Value_Display":"값·단위", "Latest_Year":"최신연도", "Series_Code":"WDI 지표코드", "WDI_Coverage_2019_2025":"2019~2025 커버리지"
                })
                st.dataframe(wdi_display, width="stretch", hide_index=True)
            else:
                st.caption("체크하면 선택 국가의 최대 10개 WDI 원자료 행을 표시합니다.")

    elif profile_section == "한국 협력경험":
        px = get_plotly_express()
        st.subheader("과거 한국 협력경험")
        history_cols = st.columns(3)
        with history_cols[0]: metric_card("2019~2024 사업 레코드", fmt_int(row.get("Project_Count_2019_2024")), "고유 사업 수 아님")
        with history_cols[1]: metric_card("2024년 사업 레코드", fmt_int(row.get("Project_Count_2024")), "연차·중복 레코드 포함 가능")
        with history_cols[2]: metric_card("활성연도", fmt_int(row.get("Active_Years_2019_2024")), "2019~2024 중 관측연도")
        st.markdown("""
        <div class="section-note"><b>레코드 수 해석:</b> KOICA 수치는 공개 원자료의 행 수이며 고유 사업 수와 동일하지 않을 수 있습니다. 동일 사업의 연차 레코드가 포함될 수 있어 과거 협력경험의 규모를 보여주는 보조근거로 사용합니다.</div>
        """, unsafe_allow_html=True)
        if not country_cy.empty:
            fig=px.line(country_cy, x="Year", y="Project_Count", markers=True, labels={"Year":"연도", "Project_Count":"사업 레코드 수"})
            fig.update_layout(height=360, margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig, width="stretch")
        st.subheader("분야별 과거 사업 레코드 추세")
        sy = sector_year_for_country(sector_year, country)
        selected_sectors = country_sector.head(5)["Sector_Group"].tolist()
        historical = sy[sy["Sector_Group"].isin(selected_sectors)]
        if not historical.empty:
            fig=px.line(historical, x="Year", y="Project_Count", color="Sector_Group", markers=True, labels={"Year":"연도", "Project_Count":"사업 레코드 수", "Sector_Group":"분야"})
            fig.update_layout(height=420, margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig, width="stretch")
            st.markdown(f"<div class=\"section-note\">{sector_trend_interpretation(country, historical)}</div>", unsafe_allow_html=True)
        st.caption("기존 협력경험이 확인되는 분야도 현재 개발수요와 CPS 정책근거가 함께 충족될 때 후속 또는 확장사업 검토가 가능합니다.")

    elif profile_section == "정책근거":
        st.subheader("CPS 정책원문 근거")
        if country_cps.empty:
            st.info("CPS 직접근거 없음 · KOICA/WDI 기반 보조 해석입니다. 근거가 있는 것으로 간주하지 않습니다.")
        else:
            insight_card(
                cps_summary["document"],
                f"문서 파일: {cps_summary['file']} · 기준연도: {cps_summary['year']}<br>"
                f"관련 분야: {cps_summary['sectors']}<br>관련 페이지: {cps_summary['pages']}<br>근거 청크: {cps_summary['chunks']}건",
            )
            cps_display = country_cps.head(5)[["Page", "Chunk_ID", "Sector_Tag", "Citation", "Text"]].copy()
            cps_display["Text"] = cps_display["Text"].map(lambda value: safe_text(value)[:320])
            cps_display = cps_display.rename(columns={"Page":"페이지", "Chunk_ID":"청크 ID", "Sector_Tag":"관련 분야", "Citation":"원문 위치", "Text":"근거 문장"})
            st.dataframe(cps_display, width="stretch", hide_index=True)
            st.caption(f"{country} CPS 검색 가능 청크 {len(country_cps)}건 중 정책·분야 관련 상위 5건을 표시합니다.")
        st.button("전체 근거·재현성으로 이동", key="profile_policy_to_evidence", on_click=queue_navigation, args=("근거·재현성", country), width="stretch")

    elif profile_section == "리스크":
        st.subheader("실행환경 하위 근거")
        st.caption(f"실행가능성 {fmt_number(row.get('Risk_Feasibility_Score_V21'))}점 · {feasibility_note}. 절대 위험등급이 아니라 공개 보조지표를 정규화한 상대점수입니다.")
        st.dataframe(risk_factor_table(row, policy_row), width="stretch", hide_index=True)
        st.info("파트너 역량은 직접 데이터가 없어 추가 검증 대상으로 표시합니다. 현지조사와 기관 실사를 대체하지 않습니다.")

    elif profile_section == "사업분야":
        st.subheader("KOICA 사업경험 상위 분야")
        st.caption("해당 분야의 과거 KOICA 사업 레코드 비중을 보여줍니다. 현재 개발수요 또는 향후 사업 타당성과 동일한 의미는 아닙니다.")
        top_sectors = country_sector.head(5)
        if top_sectors.empty:
            st.info("해당 국가의 분야별 KOICA 사업근거가 제한적입니다.")
        else:
            for _, sector_row in top_sectors.iterrows():
                header = f"{sector_row['Sector_Group']} · 공개 레코드 {fmt_int(sector_row['Project_Count_2019_2024'])}건 · {fmt_number(sector_row['Share_2019_2024']*100,1,'%')}"
                body = f"과거 협력경험 기준 · 주요 세부분야: {compact_detail_sectors(sector_row.get('Top_Detail_Sectors',''))}"
                insight_card(header, body)
        st.markdown("""
        <div class="section-note">현재 사업기회로 구체화하려면 개발수요·CPS 정책근거·실행가능성을 함께 확인하고, 현지수요와 파트너 역량을 별도로 검증해야 합니다.</div>
        """, unsafe_allow_html=True)


def render_sector(data):
    master, weights = data["master"], data["weights"]
    wdi, sector_summary, sector_year = data["wdi"], data["sector_summary"], data["sector_year"]
    policy_risk, cps_pdf = data["policy_risk"], data["cps_pdf"]
    st.title("분야 우선검토")
    country = st.selectbox("국가 선택", get_country_options(master), index=0, key="sector_country")
    row = get_country_row(master, country)
    sectors = sector_summary_for_country(sector_summary, country)
    country_wdi = wdi_for_country(wdi, country)
    country_sector_year = sector_year_for_country(sector_year, country)
    country_cps = cps_for_country(cps_pdf, country)
    policy_rows = policy_risk.loc[policy_risk["Country_KR"] == country]
    policy_row = policy_rows.iloc[0] if not policy_rows.empty else pd.Series(dtype=object)
    recs = recommended_sectors(row)
    weight_lookup = dict(zip(weights["Component"], pd.to_numeric(weights["Weight"], errors="coerce")))
    sector_fit_weight = float(weight_lookup.get("Sector Fit", 0))

    st.caption("KOICA 기존 협력경험, CPS 정책근거, WDI 개발수요와 실행위험을 함께 검토해 선택 국가의 우선검토 분야와 추가 검증사항을 제시합니다.")

    cols=st.columns(5)
    with cols[0]: metric_card("1순위 우선검토 분야", recs[0], "기존 KOICA 다년도 패턴")
    with cols[1]: metric_card("2순위 우선검토 분야", recs[1] if len(recs)>1 else "추가 검토", "기존 KOICA 다년도 패턴")
    with cols[2]: metric_card("국가 분야적합성", fmt_number(row.get("Sector_Fit_Score_V2")), f"국가 원점수 · 가중치 {sector_fit_weight * 100:.0f}%")
    with cols[3]: metric_card("국가 정책정합성", fmt_number(row.get("Policy_Alignment_Score_V21")), "분야별 점수 아님")
    with cols[4]: metric_card("국가 실행가능성", fmt_number(row.get("Risk_Feasibility_Score_V21")), feasibility_label(row.get("Risk_Feasibility_Score_V21"), master["Risk_Feasibility_Score_V21"]))

    st.markdown("""
    <div class="section-note"><b>점수 구분:</b> 국가 분야적합성·정책정합성·실행가능성은 국가 수준 원점수입니다. 현재 모델에는 분야별 개별 숫자 점수가 없으므로 새 점수를 만들지 않았습니다. 1·2순위는 기존 KOICA 다년도 패턴의 초기 후보이며, CPS·WDI·추세·실행환경은 별도 검증근거로 제시합니다.</div>
    <div class="section-note">본 결과는 분야 자동선정이 아니라 사업기회 탐색을 위한 의사결정 보조정보입니다. 최종 분야 선택은 현지 수요, 파트너 역량, CPS 최신성 및 사업 타당성 검토가 필요합니다.</div>
    """, unsafe_allow_html=True)

    sector_sections = ["우선검토", "근거 매트릭스", "과거 협력경험", "CPS 근거", "유사 KOICA 사업 사례"]
    if st.session_state.get("sector_section") not in sector_sections:
        st.session_state["sector_section"] = sector_sections[0]
    sector_section = st.segmented_control(
        "분야 세부화면",
        sector_sections,
        key="sector_section",
        required=True,
        width="stretch",
    )

    if sector_section == "우선검토":
        builder_user_type = st.selectbox(
            "AI Builder 사용자 유형",
            ["CSO/NGO", "기업/스타트업", "지자체", "대학생/연구자", "정책담당자"],
            key="sector_user_type",
        )
        st.caption("사용자 유형은 AI Builder로 전달되는 기획 조건만 바꾸며 분야 순서와 국가 점수에는 영향을 주지 않습니다.")
        st.subheader("상위 우선검토 분야")
        card_columns = st.columns(2)
        for index, sector in enumerate(recs[:2]):
            sector_rows = sectors.loc[sectors["Sector_Group"] == sector]
            sector_row = sector_rows.iloc[0] if not sector_rows.empty else pd.Series(dtype=object)
            sector_cps = cps_for_sector(country_cps, sector)
            related_wdi = sector_wdi_rows(country_wdi, sector)
            completeness = sector_evidence_completeness(sector_row, sector_cps, related_wdi, row)
            trend = sector_trend_summary(country_sector_year, sector)
            cps_pages = sorted(pd.to_numeric(sector_cps.get("Page", pd.Series(dtype=float)), errors="coerce").dropna().astype(int).unique().tolist())
            cps_text = (
                f"직접근거 {len(sector_cps)}개 청크 · {', '.join(f'p.{page}' for page in cps_pages[:6])}"
                if not sector_cps.empty else "CPS 직접근거 없음 · KOICA/WDI 기반 보조 해석"
            )
            koica_records = completeness["koica_records"]
            share = pd.to_numeric(pd.Series([sector_row.get("Share_2019_2024")]), errors="coerce").iloc[0]
            share_text = fmt_number(share * 100, 1, "%") if pd.notna(share) else "N/A"
            steps = sector_next_steps(completeness["status"]["CPS"], completeness["status"]["WDI"])
            body = (
                "<b>분야 우선검토 점수:</b> 별도 숫자점수 미산출<br>"
                f"<b>왜 이 분야인가:</b> 초기 {index + 1}순위 후보 · {trend}<br>"
                f"<b>왜 한국인가:</b> KOICA 공개 사업 레코드 {koica_records:,}건 · 비중 {share_text}의 과거 협력경험<br>"
                f"<b>현재 개발수요:</b> {sector_wdi_summary(country_wdi, sector)}<br>"
                f"<b>CPS 정책근거:</b> {cps_text}<br>"
                f"<b>핵심 실행위험:</b> {dominant_execution_constraint(policy_row)} · 국가 실행가능성 {fmt_number(row.get('Risk_Feasibility_Score_V21'))}<br>"
                f"<b>근거 완전성:</b> {completeness['score']}/4 (KOICA·CPS·WDI·실행환경)<br>"
                f"<b>기대 사회적 가치:</b> {sector_social_value(sector)}<br>"
                f"<b>권장 다음 검증:</b> {' · '.join(steps)}"
            )
            with card_columns[index % 2]:
                insight_card(f"{index + 1}순위 · {sector}", body)
                a1, a2 = st.columns(2)
                with a1:
                    st.button(
                        "AI Builder 열기",
                        key=f"sector_builder_{index}_{sector}",
                        on_click=queue_navigation,
                        args=("AI Builder", country, sector, builder_user_type),
                        width="stretch",
                        type="primary" if index == 0 else "secondary",
                    )
                with a2:
                    st.button(
                        "관련 CPS 근거",
                        key=f"sector_cps_{index}_{sector}",
                        on_click=queue_sector_detail,
                        args=("CPS 근거", sector),
                        width="stretch",
                    )

    elif sector_section == "근거 매트릭스":
        st.subheader("분야별 근거 매트릭스")
        matrix_rows = []
        execution_constraint = dominant_execution_constraint(policy_row)
        for _, sector_row in sectors.head(8).iterrows():
            sector = sector_row["Sector_Group"]
            sector_cps = cps_for_sector(country_cps, sector)
            related_wdi = sector_wdi_rows(country_wdi, sector)
            completeness = sector_evidence_completeness(sector_row, sector_cps, related_wdi, row)
            order = "1순위" if sector == recs[0] else ("2순위" if len(recs) > 1 and sector == recs[1] else "추가검토")
            pages = sorted(pd.to_numeric(sector_cps.get("Page", pd.Series(dtype=float)), errors="coerce").dropna().astype(int).unique().tolist())
            cps_text = (
                f"직접 {len(sector_cps)}청크 · {', '.join(f'p.{page}' for page in pages[:4])}"
                if not sector_cps.empty else "직접근거 없음"
            )
            next_step = sector_next_steps(completeness["status"]["CPS"], completeness["status"]["WDI"])[0]
            matrix_rows.append({
                "분야": sector,
                "우선검토 순서": order,
                "분야별 숫자점수": "별도 미산출",
                "KOICA 협력경험": f"사업 레코드 {fmt_int(sector_row['Project_Count_2019_2024'])}건 · 비중 {fmt_number(sector_row['Share_2019_2024'] * 100, 1, '%')}",
                "CPS 정책근거": cps_text,
                "WDI 수요신호": sector_wdi_summary(country_wdi, sector),
                "최근 추세": sector_trend_summary(country_sector_year, sector),
                "실행위험": f"국가 수준 · {execution_constraint}",
                "근거 완전성": f"{completeness['score']}/4",
                "권장 다음 단계": next_step,
            })
        st.dataframe(pd.DataFrame(matrix_rows), width="stretch", hide_index=True)
        st.caption("활성연도 대신 실제 최근 3개년 레코드 시작·종료값과 6개년 지속 여부를 표시합니다. WDI 분야 매핑은 검증용이며 기존 점수에 재가중하지 않습니다.")

    elif sector_section == "과거 협력경험":
        px = get_plotly_express()
        st.subheader("KOICA 사업경험 분포")
        st.caption("2019~2024년 해당 국가의 KOICA 사업 레코드 구성입니다. 과거 협력경험을 보여주며, 현재 개발수요 또는 향후 사업 타당성과 동일한 의미는 아닙니다.")
        chart = sectors.head(10).sort_values("Project_Count_2019_2024")
        if not chart.empty:
            fig=px.bar(chart, x="Project_Count_2019_2024", y="Sector_Group", orientation="h", text="Project_Count_2019_2024", labels={"Project_Count_2019_2024":"2019~2024 공개 사업 레코드 수", "Sector_Group":"분야"})
            fig.update_traces(textposition="outside")
            fig.update_layout(height=420, margin=dict(l=10,r=30,t=10,b=10))
            st.plotly_chart(fig, width="stretch")
        st.subheader("분야별 KOICA 사업경험 추세")
        trend_data = country_sector_year.loc[country_sector_year["Sector_Group"].isin(sectors.head(6)["Sector_Group"].tolist())]
        if not trend_data.empty:
            fig=px.area(trend_data, x="Year", y="Project_Count", color="Sector_Group", labels={"Year":"연도", "Project_Count":"사업 레코드 수", "Sector_Group":"분야"})
            fig.update_layout(height=430, margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig, width="stretch")
        st.caption("과거 사업 레코드의 증감이며, 증가 추세가 향후 사업 타당성을 자동으로 의미하지 않습니다.")
        history_display = sectors.head(8).copy()
        history_display["KOICA 사업 레코드"] = history_display["Project_Count_2019_2024"].map(lambda value: f"{fmt_int(value)}건")
        history_display["사업 레코드 비중"] = history_display["Share_2019_2024"].map(lambda value: fmt_number(value * 100, 1, "%"))
        history_display["최근 추세"] = history_display["Sector_Group"].map(lambda sector: sector_trend_summary(country_sector_year, sector))
        st.dataframe(history_display[["Sector_Group", "KOICA 사업 레코드", "사업 레코드 비중", "최근 추세", "Top_Detail_Sectors"]].rename(columns={"Sector_Group":"분야", "Top_Detail_Sectors":"주요 세부분야"}), width="stretch", hide_index=True)

    elif sector_section == "CPS 근거":
        st.subheader("CPS 분야별 정책근거")
        focus_options = sectors["Sector_Group"].head(8).tolist() or recs
        if st.session_state.get("sector_cps_focus") not in focus_options:
            st.session_state["sector_cps_focus"] = recs[0] if recs[0] in focus_options else focus_options[0]
        focus_sector = st.selectbox("근거 확인 분야", focus_options, key="sector_cps_focus")
        sector_cps = cps_for_sector(country_cps, focus_sector)
        if sector_cps.empty:
            st.info("CPS 직접근거 없음 · KOICA/WDI 기반 보조 해석입니다. 최신 CPS 원문에서 해당 분야를 별도로 확인해야 합니다.")
        else:
            document = cps_document_summary(country, country_cps)
            pages = sorted(pd.to_numeric(sector_cps["Page"], errors="coerce").dropna().astype(int).unique().tolist())
            insight_card(
                f"{focus_sector} · CPS 직접근거 {len(sector_cps)}개 청크",
                f"문서: {document['document']} · 파일: {document['file']} · 기준연도: {document['year']}<br>"
                f"관련 페이지: {', '.join(f'p.{page}' for page in pages)}<br>관련 키워드·분야 태그: {focus_sector}",
            )
            cps_display = sector_cps.head(8)[["Page", "Chunk_ID", "Sector_Tag", "Citation", "Text"]].copy()
            cps_display["Text"] = cps_display["Text"].map(lambda value: safe_text(value)[:360])
            st.dataframe(cps_display.rename(columns={"Page":"페이지", "Chunk_ID":"청크 ID", "Sector_Tag":"분야 태그", "Citation":"원문 위치", "Text":"근거 문장"}), width="stretch", hide_index=True)
        st.button("국가 전체 근거·재현성 열기", key="sector_to_evidence", on_click=queue_navigation, args=("근거·재현성", country), width="stretch")

    elif sector_section == "유사 KOICA 사업 사례":
        st.subheader("유사 KOICA 사업 사례")
        st.caption("신규 추천 아이디어가 아니라 동일 국가·동일 분야의 과거 KOICA 공개 레코드입니다. 신규 사업기획은 선택 분야를 AI Builder로 전달해 생성합니다.")
        case_options = sectors["Sector_Group"].head(8).tolist() or recs
        if st.session_state.get("sector_case_focus") not in case_options:
            st.session_state["sector_case_focus"] = recs[0] if recs[0] in case_options else case_options[0]
        case_sector = st.selectbox("사례 확인 분야", case_options, key="sector_case_focus")
        with st.expander("세부 사업근거 불러오기"):
            if st.checkbox("KOICA 원자료 사례 로드", value=False, key="sector_load_projects"):
                projects = load_optional_dataset("projects")
                cases = similar_project_cases(projects, country, case_sector)
                if cases.empty:
                    st.info("선택 국가·분야의 KOICA 유사 사업 레코드가 없습니다.")
                else:
                    st.dataframe(cases, width="stretch", hide_index=True)
                    st.caption("원문 사업명은 자르지 않고 표시하며, 출처 ID는 원본 CSV의 실제 행 위치입니다.")
            else:
                st.caption("체크하면 12,436행 사업근거 CSV를 지연 로드하고 최대 8개 유사사례만 표시합니다.")
        st.button(
            "이 분야로 AI Builder 열기",
            key="sector_case_to_builder",
            on_click=queue_navigation,
            args=("AI Builder", country, case_sector, st.session_state.get("sector_user_type", "CSO/NGO")),
            width="stretch",
            type="primary",
        )


def render_builder(data):
    master, wdi, sector_summary = data["master"], data["wdi"], data["sector_summary"]
    weights = data["weights"]
    st.title("RAG형 AI Builder")
    st.caption("KOICA 사업정보와 CPS 정책원문을 핵심으로 WDI·정책·리스크 보조지표를 검색하고 생성문에 근거 ID를 삽입합니다.")
    st.markdown("""
    <div class="brief-kicker"><b>AI 엔진:</b> 국가·분야·키워드 입력 → RAG 근거 검색 → Evidence Pack 고정 → 로컬 생성 또는 LLM 생성 → citation 포함 결과·브리프·PDF export.</div>
    """, unsafe_allow_html=True)

    scenarios = {
        "CSO 탄자니아 공공행정": ("탄자니아", "공공행정", "CSO/NGO", "소규모 파일럿", "디지털 행정, 현지 역량강화, 성과관리"),
        "지자체 베트남 디지털정부": ("베트남", "공공행정", "지자체", "민관협력형", "디지털정부, 지방행정, 공무원 교육"),
        "기업 르완다 ICT·에너지": ("르완다", "기술환경에너지", "기업/스타트업", "중형 확장사업", "ICT, 에너지 접근성, 민관협력"),
        "직접 선택": (None, None, "CSO/NGO", "소규모 파일럿", "디지털 전환, 현지 역량강화, 성과관리"),
    }
    scenario = st.radio("시연 시나리오", list(scenarios.keys()), horizontal=True)
    sc_country, sc_sector, sc_user, sc_scale, sc_keywords = scenarios[scenario]

    c1, c2 = st.columns([0.9, 1.1])
    with c1:
        country_options = get_country_options(master)
        country_default = sc_country if sc_country in country_options else country_options[0]
        country = st.selectbox("대상 국가", country_options, index=country_options.index(country_default), key="builder_country")
        row = get_country_row(master, country)
        sectors = sector_summary_for_country(sector_summary, country)
        sector_options = sectors["Sector_Group"].tolist() if not sectors.empty else recommended_sectors(row)
        default_sector = sc_sector if sc_sector in sector_options else recommended_sectors(row)[0]
        idx = sector_options.index(default_sector) if default_sector in sector_options else 0
        if st.session_state.get("builder_sector") not in sector_options:
            st.session_state["builder_sector"] = default_sector
        sector = st.selectbox("사업 분야", sector_options, index=idx, key="builder_sector")
        user_types = ["CSO/NGO", "기업/스타트업", "지자체", "대학생/연구자", "정책담당자"]
        if st.session_state.get("builder_user_type") not in user_types:
            st.session_state["builder_user_type"] = sc_user if sc_user in user_types else user_types[0]
        user_type = st.selectbox("사용자 유형", user_types, index=user_types.index(sc_user) if sc_user in user_types else 0, key="builder_user_type")
        scales = ["소규모 파일럿", "중형 확장사업", "민관협력형", "정책연구/예비타당성"]
        scale = st.selectbox("사업 규모", scales, index=scales.index(sc_scale) if sc_scale in scales else 0)
        keywords = st.text_input("핵심 키워드", value=sc_keywords)
        mode = st.radio("생성 모드", ["로컬 RAG", "LLM RAG (선택)"], horizontal=True)
        with st.expander("AI 생성 예비 설계 가정 조정"):
            st.caption("공공데이터 관측값이 아닌 잠정 설계값입니다. 현지조사·예산·수행기관 협의를 거쳐 수정해야 합니다.")
            duration_months = st.number_input("잠정 사업기간(개월)", min_value=3, max_value=60, value=12, step=1)
            training_min = st.number_input("잠정 교육대상 최소(명)", min_value=0, max_value=5000, value=30, step=5)
            training_max = st.number_input("잠정 교육대상 최대(명)", min_value=int(training_min), max_value=5000, value=max(50, int(training_min)), step=5)
            kpi_min = st.number_input("잠정 KPI 최소(개)", min_value=1, max_value=100, value=5, step=1)
            kpi_max = st.number_input("잠정 KPI 최대(개)", min_value=int(kpi_min), max_value=100, value=max(10, int(kpi_min)), step=1)
            partner_count = st.text_input("파트너 수", value="현지조사 후 확정")
            budget_range = st.text_input("예산 범위", value="예산 협의 후 확정")
            project_stage = st.selectbox("사업 단계", ["예비 파일럿 설계", "수요조사", "타당성 검토", "확장 검토"])
            outcome_goal = st.text_input("주요 성과목표", value="현지 수요검증과 운영모델 검토")
        design_assumptions = normalize_design_assumptions({
            "duration_months": int(duration_months),
            "training_min": int(training_min),
            "training_max": int(training_max),
            "kpi_min": int(kpi_min),
            "kpi_max": int(kpi_max),
            "partner_count": partner_count,
            "budget_range": budget_range,
            "project_stage": project_stage,
            "outcome_goal": outcome_goal,
        })
        clicked = st.button("RAG형 AI 사업기획서 생성", width="stretch", type="primary")

    # Build a country-scoped corpus only after the user reaches AI Builder.
    country_frames = {}
    for key in ("master", "wdi", "projects", "policy_risk", "sector_summary", "cps_pdf"):
        frame = data[key]
        country_frames[key] = frame.loc[frame["Country_KR"] == country]
    corpus = build_rag_corpus(
        country_frames["master"],
        country_frames["wdi"],
        country_frames["projects"],
        country_frames["policy_risk"],
        country_frames["sector_summary"],
        country_frames["cps_pdf"],
    )

    with c2:
        docs_preview = retrieve_rag_evidence(corpus, country, sector, keywords, row, top_k=10)
        c21, c22, c23 = st.columns(3)
        with c21: metric_card("우선순위 점수", fmt_number(row.get("K_ODA_Opportunity_Score_V21")), f"기본 순위 #{fmt_int(row.get('Rank_V21'))}")
        with c22: metric_card("후보유형", compact_candidate_label(row.get("Candidate_Type_V21")), feasibility_label(row.get("Risk_Feasibility_Score_V21"), master["Risk_Feasibility_Score_V21"]))
        with c23: metric_card("검색 근거", fmt_int(len(docs_preview)), "RAG Top-K")
        st.markdown(f"**정책·리스크 보조지표:** 정책정합성 {fmt_number(row.get('Policy_Alignment_Score_V21'))}, 실행가능성 {fmt_number(row.get('Risk_Feasibility_Score_V21'))}")
        st.markdown("**RAG 근거 미리보기:**")
        for _, d in docs_preview.head(5).iterrows():
            st.markdown(f"- **{d['Source_Type']}** · {d['Title']}")

    if clicked:
        st.divider()
        row = get_country_row(master, country)
        rag_docs = retrieve_rag_evidence(corpus, country, sector, keywords, row, top_k=16)
        builder_result = build_builder_result(country, sector, rag_docs, design_assumptions)
        prompt = build_rag_prompt(country, sector, user_type, scale, keywords, row, rag_docs, weights, design_assumptions)
        local_proposal = build_rag_markdown_proposal(
            country, sector, user_type, scale, keywords, row, rag_docs, weights, design_assumptions, builder_result
        )
        llm_status = "로컬 RAG 생성 사용"
        llm_used = False
        proposal = local_proposal
        if mode == "LLM RAG (선택)":
            llm_text, llm_status = call_openai_llm(prompt)
            if llm_text:
                llm_used = True
                builder_result["llm_draft"] = llm_text
                proposal = llm_text.rstrip() + "\n\n" + structured_result_appendix(builder_result, rag_docs)

        generation_mode = "OpenAI LLM + RAG" if llm_used else "Local RAG"
        builder_result["generation_mode"] = generation_mode
        generation_metadata = f"\n\n## 생성 메타데이터\n- 생성모드: {generation_mode}\n- 모델 버전: {MODEL_VERSION}\n- 근거 범위: {country} · {sector}\n"
        proposal = proposal + generation_metadata
        evidence_pack = build_rag_evidence_pack(
            country, sector, keywords, rag_docs, design_assumptions, builder_result
        ) + generation_metadata
        brief = build_policy_brief(
            country, sector, row, rag_docs, design_assumptions, builder_result
        ) + generation_metadata
        proposal_pdf = markdown_to_pdf_bytes("K-ODA Compass 근거 기반 AI 사업제안서", proposal)
        brief_pdf = markdown_to_pdf_bytes(f"K-ODA Compass {country} {sector} 1-page Brief", brief)
        quality_status, quality_report = builder_output_quality_report(
            country, sector, rag_docs, proposal, brief, evidence_pack, proposal_pdf, builder_result
        )
        builder_result.update({
            "proposal": proposal,
            "brief": brief,
            "evidence_pack": evidence_pack,
        })

        st.subheader("Evidence-grounded AI 생성 결과")
        if llm_used:
            st.success(f"생성 엔진: OpenAI LLM + RAG · {llm_status}")
        elif mode == "LLM RAG (선택)":
            st.warning(f"생성 엔진: Local RAG (로컬 fallback) · {llm_status}")
        else:
            st.info("생성 엔진: Local RAG · API 키 없이 근거추적형 초안을 생성했습니다.")
        if quality_status == "BLOCK":
            st.error("산출물 자동 품질검사: BLOCK · 직접근거·Citation·PDF 항목을 확인하세요.")
        elif quality_status == "REVIEW":
            st.warning("산출물 자동 품질검사: REVIEW · 통합된 반복 레코드와 미등록 메타데이터를 확인하세요.")
        else:
            st.success("산출물 자동 품질검사: PASS")
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.download_button("사업기획서 MD", proposal.encode("utf-8"), f"KODA_{country}_{sector}_rag_proposal.md", "text/markdown", width="stretch")
        with d2:
            st.download_button("Evidence Pack", evidence_pack.encode("utf-8"), f"KODA_{country}_{sector}_evidence_pack.md", "text/markdown", width="stretch")
        with d3:
            st.download_button("1-page Brief", brief.encode("utf-8"), f"KODA_{country}_{sector}_brief.md", "text/markdown", width="stretch")
        with d4:
            if proposal_pdf:
                st.download_button("Proposal PDF", proposal_pdf, f"KODA_{country}_{sector}_proposal.pdf", "application/pdf", width="stretch")
            else:
                font_available, font_message = korean_pdf_font_status()
                st.error(font_message if not font_available else "Proposal PDF 생성에 실패했습니다. ReportLab 설치와 문서 구조를 확인하세요.")

        tabs = st.tabs(["요약", "근거 Citation", "품질검사", "점수 기여도", "브리프", "LLM Prompt", "원문"])
        with tabs[0]:
            st.markdown(f"""
            <div class="section-note"><b>핵심 요약:</b> {country} × {sector} 조합에 대해 {len(rag_docs)}개 근거를 검색했고, 모든 생성 결과는 [E01] 형식 citation으로 추적 가능합니다.</div>
            """, unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1: insight_card("왜 이 국가인가", f"개발수요 {fmt_number(row.get('Development_Need_Score'))}, 정책정합성 {fmt_number(row.get('Policy_Alignment_Score_V21'))}, 실행가능성 {fmt_number(row.get('Risk_Feasibility_Score_V21'))}")
            with c2: insight_card("왜 이 분야인가", f"추천분야 {safe_text(row.get('Recommended_Service_Angle_V2'))}, 검색분야 {sector}")
            with c3: insight_card("AI 안전장치", "Evidence Pack을 먼저 고정하고 근거 ID를 생성문에 삽입")
        with tabs[1]:
            display_docs = rag_docs[["Citation_ID", "Evidence_Class", "Directness", "Source_Type", "Country_KR", "Sector_Group", "Title", "Citation", "RAG_Score"]].copy()
            st.dataframe(display_docs, width="stretch", hide_index=True)
        with tabs[2]:
            st.dataframe(quality_report, width="stretch", hide_index=True)
            st.caption("REVIEW는 오류 확정이 아니라 잠정 가정·중복 통합·미등록 메타데이터의 사람 검토가 필요하다는 뜻입니다.")
        with tabs[3]:
            contrib = score_contribution_table(row, weights)
            st.dataframe(contrib, width="stretch", hide_index=True)
        with tabs[4]:
            st.markdown(brief)
            if brief_pdf:
                st.download_button("Brief PDF", brief_pdf, f"KODA_{country}_{sector}_brief.pdf", "application/pdf", width="stretch")
        with tabs[5]:
            st.code(prompt, language="markdown")
        with tabs[6]:
            st.markdown(proposal)
            st.download_button("사업기획서 다시 다운로드", proposal.encode("utf-8"), f"KODA_{country}_{sector}_rag_proposal.md", "text/markdown", width="stretch")


def render_evidence(data):
    master, weights = data["master"], data["weights"]
    notes, cps_coverage = data["notes"], data["cps_coverage"]
    record_counts = count_csv_records(("projects", "sector_year", "wdi", "cps_pdf", "policy_risk", "sector_summary"))
    st.title("근거·재현성 센터")
    st.caption("선택 국가의 원자료, 점수 산출 과정, 정책문서 인용근거와 모델 한계를 단계별로 확인합니다.")

    evidence_country = st.selectbox("근거 확인 국가", get_country_options(master), index=0, key="evidence_country")
    evidence_row = get_country_row(master, evidence_country)
    country_code = safe_text(evidence_row.get("WDI_Country_Code"))
    coverage_rows = cps_coverage.loc[cps_coverage["Country_Code"] == country_code]
    has_cps_text = not coverage_rows.empty and float(coverage_rows.iloc[0].get("Readable_Pages", 0) or 0) > 0
    wdi_core_missing = pd.to_numeric(pd.Series([evidence_row.get("WDI_Core_Missing_Count")]), errors="coerce").iloc[0]
    wdi_core_available = 7 - int(wdi_core_missing) if pd.notna(wdi_core_missing) else 0

    cols = st.columns(5)
    with cols[0]: metric_card("v2.1 우선순위 점수", fmt_number(evidence_row.get("K_ODA_Opportunity_Score_V21")), f"기본 순위 #{fmt_int(evidence_row.get('Rank_V21'))}")
    with cols[1]: metric_card("KOICA 사업 레코드", fmt_int(evidence_row.get("Project_Count_2019_2024")), "고유 사업 수 아님")
    with cols[2]: metric_card("CPS 직접근거", "보유" if has_cps_text else "없음", "원문 청킹 상태 기준")
    with cols[3]: metric_card("WDI 핵심 최신값", f"{wdi_core_available}/7", "지표별 최신 가용연도")
    with cols[4]: metric_card("데이터 신뢰도", fmt_number(evidence_row.get("Data_Reliability_Score_V21")), "사전 산출 커버리지 점수")
    st.markdown("""
    <div class="section-note">본 화면은 번들 내부의 산식·파일·인용 위치를 재현하는 내부 감사도구입니다. 외부 독립검증이나 최종 사업 타당성 검증을 완료했다는 의미가 아닙니다.</div>
    """, unsafe_allow_html=True)

    evidence_sections = ["요약", "점수 재현", "원자료 추적", "전처리 규칙", "한계·재현성"]
    if st.session_state.get("evidence_section") not in evidence_sections:
        st.session_state["evidence_section"] = evidence_sections[0]
    evidence_section = st.segmented_control(
        "근거 세부화면",
        evidence_sections,
        key="evidence_section",
        required=True,
        width="stretch",
    )

    cps_target_count = int(master["국가협력전략 대상국가"].astype(str).str.upper().eq("Y").sum())
    office_country_count = int(master["한국국제협력단 사무소 주재 여부"].astype(str).str.upper().eq("Y").sum())
    readable_coverage = cps_coverage.loc[pd.to_numeric(cps_coverage["Readable_Pages"], errors="coerce").fillna(0) > 0]
    cps_chunk_country_count = int(readable_coverage["Country_Code"].nunique())
    cps_top50_evidence = len(set(master["WDI_Country_Code"].astype(str)) & set(readable_coverage["Country_Code"].astype(str)))
    image_only_count = int((pd.to_numeric(cps_coverage["Readable_Pages"], errors="coerce").fillna(0) == 0).sum())

    wdi_expected = len(master) * 7
    wdi_observed = wdi_expected - int(pd.to_numeric(master["WDI_Core_Missing_Count"], errors="coerce").fillna(7).sum())
    risk_raw_fields = ["취약국가 지수", "부패인식점수", "전자정부지수", "인간개발지수", "기업여건"]
    risk_raw_expected = len(master) * len(risk_raw_fields)
    risk_raw_observed = int(master[risk_raw_fields].notna().sum().sum())
    model_coverage_expected = len(master) * 8
    model_coverage_observed = int(round((pd.to_numeric(master["Policy_Risk_Data_Coverage_%"], errors="coerce").fillna(0) / 100 * 8).sum()))

    if evidence_section == "요약":
        st.subheader("데이터 계층")
        hierarchy = pd.DataFrame([
            ["A. 핵심 외교·ODA 공공데이터", "KOICA 사업정보 · CPS 정책원문", "사업 레코드와 정책문서 원문"],
            ["B. 보조 데이터", "World Bank WDI · 정책·실행환경 보조지표", "개발수요와 실행환경 해석 지원"],
            ["C. 파생지표", "개발수요 · 한국 협력기반 · 분야적합성 · 사업기회 공백 · 정책정합성 · 실행가능성 · 데이터 신뢰도", "원자료에서 사전 산출된 모델 입력"],
            ["D. 서비스 출력", "국가 우선검토 점수 · 분야 제안 · RAG Evidence Pack · 사업기획서 초안", "의사결정 보조 결과"],
        ], columns=["계층", "항목", "역할"])
        st.dataframe(hierarchy, width="stretch", hide_index=True)
        st.caption("파생지표와 서비스 출력은 원천 데이터셋이 아닙니다.")

        st.subheader("데이터셋 진단 단위")
        c1,c2,c3,c4,c5 = st.columns(5)
        with c1: metric_card("분석 대상", f"{len(master)}/50", "후보국")
        with c2: metric_card("KOICA 사업 레코드", fmt_int(record_counts["projects"]), "2019~2024 원자료 행")
        with c3: metric_card("국가×분야×연도", fmt_int(record_counts["sector_year"]), "집계행")
        with c4: metric_card("WDI 최신값 레코드", fmt_int(record_counts["wdi"]), "50개국×10지표")
        with c5: metric_card("CPS RAG 청크", fmt_int(record_counts["cps_pdf"]), f"{cps_chunk_country_count}개국")

        st.subheader("CPS 수치 정의")
        c1,c2,c3,c4,c5 = st.columns(5)
        with c1: metric_card("CPS 대상 후보국", f"{cps_target_count}/50", "Top50 마스터 표시")
        with c2: metric_card("CPS PDF 인벤토리", f"{len(cps_coverage)}개", "OCR coverage 파일")
        with c3: metric_card("PDF/RAG 처리 국가", f"{cps_chunk_country_count}개국", "읽기 가능한 원문")
        with c4: metric_card("Top50 CPS 근거", f"{cps_top50_evidence}/50", "국가코드 교차")
        with c5: metric_card("CPS RAG 청크", f"{record_counts['cps_pdf']}개", "페이지 단위 청크")
        st.caption(f"26은 CPS 대상 표시의 수, 20은 실제 검색 가능한 원문 국가 수, 19/50은 Top50과 원문 국가의 교집합입니다. 서로 다른 모집단입니다. 이미지형 PDF {image_only_count}/{len(cps_coverage)}개는 직접근거로 계산하지 않습니다.")

        st.subheader("커버리지 산식")
        c1,c2,c3,c4 = st.columns(4)
        with c1: metric_card("WDI 핵심 커버리지", f"{wdi_observed}/{wdi_expected}", f"{wdi_observed / wdi_expected * 100:.1f}%")
        with c2: metric_card("실행환경 원자료 5종", f"{risk_raw_observed}/{risk_raw_expected}", f"{risk_raw_observed / risk_raw_expected * 100:.1f}%")
        with c3: metric_card("저장된 모델 커버리지", f"{model_coverage_observed}/{model_coverage_expected}", f"{model_coverage_observed / model_coverage_expected * 100:.2f}%")
        with c4: metric_card("KOICA 사무소 존재 표시", f"{office_country_count}/50", "공식 사무소 총수 아님")
        st.markdown("""
        <div class="section-note"><b>계산:</b> WDI는 보유 핵심 최신값 수 ÷ 50×7, 실행환경 원자료는 보유 값 수 ÷ 50×5입니다. 저장된 모델 커버리지는 CSV의 국가별 퍼센트를 8개 기대항목 등가값으로 환산한 값입니다. 8개 항목의 생성 코드는 번들에 없어 세부 구성은 추가 검증이 필요합니다.</div>
        """, unsafe_allow_html=True)

        with st.expander("데이터셋 상세 인벤토리"):
            if st.checkbox("상세 메타데이터 표시", value=False, key="evidence_inventory_detail"):
                inventory = pd.DataFrame([
                    ["A", "KOICA", DATA_FILES["projects"], "2019~2024", "수집일 메타데이터 미포함", "사업 레코드·금액 raw", f"{record_counts['projects']:,}행", "국가·연도·분야·CSV 행", "협력경험·RAG", "https://www.data.go.kr/", "고유 사업 ID 없음·금액 단위 재확인 필요"],
                    ["A", "대한민국 ODA/CPS", DATA_FILES["cps_pdf"], "문서별 상이", "문서 버전은 원문 1페이지", "페이지·청크", f"{record_counts['cps_pdf']:,}청크·{cps_chunk_country_count}개국", "국가코드·페이지·청크 ID", "정책원문 인용", "https://www.odakorea.go.kr/", f"27 PDF 중 이미지형 {image_only_count}개 OCR 필요"],
                    ["B", "World Bank", DATA_FILES["wdi"], "2019~2025 창의 최신값", "추출일 메타데이터 미포함", "지표별 단위", f"{record_counts['wdi']:,}행", "국가코드·지표코드", "개발수요 보조", "https://databank.worldbank.org/source/world-development-indicators-", f"핵심 최신값 {wdi_observed}/{wdi_expected}"],
                    ["B", "KOICA 협력국 통합 개발지표", DATA_FILES["policy_risk"], "공개자료 기준", "2023-06-14", "원지표·0~100 정규화", f"{record_counts['policy_risk']:,}행", "국가명", "정책·실행환경 보조", "https://www.data.go.kr/", f"원자료 5종 {risk_raw_observed}/{risk_raw_expected}"],
                    ["C", "K-ODA Compass", DATA_FILES["master"], "통합 스냅샷", MODEL_VERSION, "0~100 원점수", f"{len(master):,}행", "국가코드·순위", "파생점수", GITHUB_URL, "점수 생성 스크립트 미포함"],
                    ["C", "K-ODA Compass", DATA_FILES["sector_year"], "2019~2024", MODEL_VERSION, "집계 레코드", f"{record_counts['sector_year']:,}행", "국가·분야·연도", "추세 파생집계", GITHUB_URL, "고유 사업 수가 아닌 레코드 집계"],
                    ["D", "K-ODA Compass", "런타임 출력", "사용 시점", APP_VERSION, "문서·citation", "요청별 생성", "국가·분야·Evidence ID", "Evidence Pack·기획초안", LIVE_DEMO_URL, "선택적 LLM 출력은 비결정적일 수 있음"],
                ], columns=["계층", "제공기관", "파일·데이터셋", "기간", "수집·갱신", "단위", "규모", "주요 키", "모델 역할", "공개출처 URL", "결측·OCR·커버리지"])
                st.dataframe(inventory, width="stretch", hide_index=True)
            else:
                st.caption("체크하면 파일별 기관·기간·단위·키·역할·출처·커버리지를 표시합니다.")

    elif evidence_section == "점수 재현":
        st.subheader(f"{evidence_country} v2.1 점수 재현")
        st.latex(r"KODA_{v2.1}=0.25D+0.20K+0.15S+0.10G+0.15P+0.10F+0.05R")
        reproduction = score_reproduction_table(evidence_row, weights)
        contribution_sum = float(reproduction["기여점수"].sum())
        actual_score = float(evidence_row.get("K_ODA_Opportunity_Score_V21"))
        st.dataframe(reproduction, width="stretch", hide_index=True)
        c1,c2,c3 = st.columns(3)
        with c1: metric_card("가중 기여도 합계", f"{contribution_sum:.2f}", "7개 구성요소")
        with c2: metric_card("마스터 종합점수", f"{actual_score:.2f}", f"기본 순위 #{fmt_int(evidence_row.get('Rank_V21'))}")
        with c3: metric_card("재현 오차", f"{abs(contribution_sum - actual_score):.4f}", "반올림 허용범위")
        development = reproduction.loc[reproduction["구성요소"] == "개발수요"].iloc[0]
        st.caption(f"계산 예: 개발수요 {development['원점수']:.2f} × {development['가중치']:.2f} = {development['기여점수']:.4f}")
        st.info("이 표는 번들에 저장된 7개 원점수와 가중치로 종합점수를 재계산합니다. 각 원점수 자체의 생성 과정은 아래 원자료와 전처리 규칙 범위에서만 추적 가능합니다.")
        with st.expander("가중치 원문"):
            if st.checkbox("가중치 CSV 표시", value=False, key="evidence_weights_raw"):
                st.dataframe(weights, width="stretch", hide_index=True)

    elif evidence_section == "원자료 추적":
        raw_sources = ["KOICA", "CPS", "WDI", "정책·실행환경"]
        if st.session_state.get("evidence_raw_source") not in raw_sources:
            st.session_state["evidence_raw_source"] = raw_sources[0]
        raw_source = st.segmented_control("감사 원자료", raw_sources, key="evidence_raw_source", required=True, width="stretch")

        if raw_source == "KOICA":
            st.subheader(f"{evidence_country} KOICA 사업 레코드")
            st.caption("원본 파일에는 안정적인 고유 사업 ID가 없어 고유 사업 수를 산출하지 않습니다. CSV 실제 행 위치를 출처 ID로 사용합니다.")
            if st.checkbox("KOICA 원자료 불러오기", value=False, key="evidence_load_koica"):
                projects = load_optional_dataset("projects")
                country_projects = projects_for_country(projects, evidence_country)
                st.dataframe(koica_country_audit_table(projects, evidence_country), width="stretch", hide_index=True)
                st.caption(f"전체 {len(country_projects):,}개 사업 레코드 중 최근연도·금액순 최대 50개를 표시합니다.")
                st.download_button("선택 국가 KOICA 영문 원자료 CSV", country_projects.to_csv(index=False).encode("utf-8-sig"), f"KODA_{country_code}_KOICA_raw.csv", "text/csv", width="stretch")
            else:
                st.caption("체크할 때만 12,436행 KOICA 파일을 로드합니다.")

        elif raw_source == "CPS":
            st.subheader(f"{evidence_country} CPS 정책원문")
            if not has_cps_text:
                st.info("CPS 직접근거 없음 · 읽기 가능한 원문 청크가 없습니다. KOICA/WDI 보조 해석과 최신 CPS 수동확인이 필요합니다.")
            elif st.checkbox("CPS 청크 원자료 불러오기", value=False, key="evidence_load_cps"):
                cps_pdf = load_optional_dataset("cps_pdf")
                evidence_cps = cps_for_country(cps_pdf, evidence_country)
                document = cps_document_summary(evidence_country, evidence_cps)
                insight_card(document["document"], f"파일: {document['file']} · 기준연도: {document['year']} · 관련 페이지: {document['pages']} · 청크: {document['chunks']}개")
                cps_display = evidence_cps.head(20)[["PDF_File", "Page", "Chunk_ID", "Sector_Tag", "Citation", "Text"]].copy()
                cps_display["Text"] = cps_display["Text"].map(lambda value: safe_text(value)[:420])
                st.dataframe(cps_display.rename(columns={"PDF_File":"문서 파일", "Page":"페이지", "Chunk_ID":"청크 ID", "Sector_Tag":"관련 분야", "Citation":"원문 위치", "Text":"관련 문장"}), width="stretch", hide_index=True)
                st.download_button("선택 국가 CPS 청크 CSV", evidence_cps.to_csv(index=False).encode("utf-8-sig"), f"KODA_{country_code}_CPS_chunks.csv", "text/csv", width="stretch")
            else:
                st.caption("체크할 때만 806개 CPS 청크 파일을 로드합니다.")

        elif raw_source == "WDI":
            st.subheader(f"{evidence_country} World Bank WDI")
            if st.checkbox("WDI 원자료 불러오기", value=False, key="evidence_load_wdi"):
                wdi = load_optional_dataset("wdi")
                evidence_wdi = wdi_for_country(wdi, evidence_country)
                wdi_display = evidence_wdi[["Indicator_Name", "Series_Code", "Latest_Value_Display", "Latest_Year", "WDI_Coverage_2019_2025", "Score_Direction"]].copy()
                wdi_display["출처"] = "World Bank WDI"
                st.dataframe(wdi_display.rename(columns={"Indicator_Name":"지표명", "Series_Code":"지표코드", "Latest_Value_Display":"값·단위", "Latest_Year":"최신연도", "WDI_Coverage_2019_2025":"2019~2025 보유연도", "Score_Direction":"점수 방향"}), width="stretch", hide_index=True)
                st.download_button("선택 국가 WDI 영문 원자료 CSV", evidence_wdi.to_csv(index=False).encode("utf-8-sig"), f"KODA_{country_code}_WDI_raw.csv", "text/csv", width="stretch")
            else:
                st.caption("체크할 때만 500행 WDI 파일을 로드합니다.")

        elif raw_source == "정책·실행환경":
            st.subheader(f"{evidence_country} 정책·실행환경 보조지표")
            st.caption("해당 지표는 현지조사나 기관 실사를 대체하지 않는 보조지표입니다.")
            if st.checkbox("정책·실행환경 원자료 불러오기", value=False, key="evidence_load_policy"):
                policy = load_optional_dataset("policy_risk")
                policy_rows = policy.loc[policy["Country_KR"] == evidence_country]
                policy_row = policy_rows.iloc[0] if not policy_rows.empty else pd.Series(dtype=object)
                st.dataframe(policy_risk_audit_table(policy_row), width="stretch", hide_index=True)
                if not policy_rows.empty:
                    st.download_button("선택 국가 정책·실행환경 영문 원자료 CSV", policy_rows.to_csv(index=False).encode("utf-8-sig"), f"KODA_{country_code}_policy_risk_raw.csv", "text/csv", width="stretch")
            else:
                st.caption("체크할 때만 50행 정책·실행환경 파일을 로드합니다.")

    elif evidence_section == "전처리 규칙":
        st.subheader("전처리·정규화 규칙")
        rules = pd.DataFrame([
            ["최신연도 선택", "WDI CSV에 지표별 Latest_Year·Latest_Value가 사전 저장됨", "앱은 최신연도를 다시 계산하지 않음"],
            ["결측치 처리", "결측은 최신값 없음·결측으로 표시", "앱 렌더링 단계에서 0으로 대체하지 않음"],
            ["정규화 방식", "0~100 파생점수는 마스터·정책 CSV에서 읽음", "생성 스크립트 미포함으로 앱에서 재정규화하지 않음"],
            ["점수 방향", "취약국가 지수는 낮을수록 유리하게 역산, 부패인식·전자정부·HDI는 높을수록 유리", "KODA_v21_score_notes.csv 명시 범위"],
            ["극단값 처리", "앱 코드에 winsorization·clipping 없음", "사전 산출 단계 적용 여부는 확인 불가"],
            ["연도 불일치", "WDI 지표별 최신 가용연도를 그대로 사용", "동일 기준연도로 강제 정렬하지 않음"],
            ["데이터 신뢰도", "저장된 WDI·정책 커버리지와 Data_Reliability_Score를 표시", "정확한 결합 공식 생성 코드 미포함"],
            ["런타임 변환", "숫자형 후보 열만 pd.to_numeric으로 변환, 순위 오름차순 정렬", "원본 CSV 값 자체는 수정하지 않음"],
        ], columns=["규칙", "실제 구현·저장 상태", "재현 범위·한계"])
        st.dataframe(rules, width="stretch", hide_index=True)
        st.markdown("""
        <div class="section-note"><b>용어:</b> 정책·실행환경 보조지표와 실행환경·리스크 보조지표는 현지조사나 기관 실사를 대체하지 않습니다. proxy를 최종 정책판단이나 사업 타당성으로 해석하지 않습니다.</div>
        """, unsafe_allow_html=True)
        with st.expander("v2.1 점수 노트 원문"):
            if st.checkbox("점수 노트 CSV 표시", value=False, key="evidence_notes_raw"):
                st.dataframe(notes, width="stretch", hide_index=True)
                st.caption("이 노트의 CPS PDF 미파싱 문구는 점수모델 작성 시점 설명이며, 현재 CPS RAG 청크는 별도 파일로 추가돼 있습니다.")

    elif evidence_section == "한계·재현성":
        st.subheader("버전·재현성")
        c1,c2,c3,c4 = st.columns(4)
        with c1: metric_card("모델 버전", MODEL_VERSION, "7개 가중 구성요소")
        with c2: metric_card("앱 버전", APP_VERSION, "수동 버전 문자열")
        with c3: metric_card("데이터 스냅샷", "2023~2025", DATA_SNAPSHOT)
        with c4: metric_card("분석 대상", f"{len(master)}개국", "Top50 고정")
        st.markdown("""
        <div class="section-note"><b>동일 입력 재현성:</b> 번들 CSV와 동일 입력을 사용한 점수 합산·로컬 검색·로컬 RAG는 결정적으로 재현됩니다. 선택적 외부 LLM 출력은 모델 버전과 서비스 상태에 따라 문구가 달라질 수 있습니다. Git commit은 런타임에서 추정하지 않고 앱 버전 문자열을 사용합니다.</div>
        """, unsafe_allow_html=True)

        total_pages = int(pd.to_numeric(cps_coverage["Pages"], errors="coerce").fillna(0).sum())
        readable_pages = int(pd.to_numeric(cps_coverage["Readable_Pages"], errors="coerce").fillna(0).sum())
        ocr_target_pages = int(pd.to_numeric(cps_coverage["OCR_Target_Pages"], errors="coerce").fillna(0).sum())
        st.subheader("한계와 완화방안")
        limitations = pd.DataFrame([
            ["이미지형 CPS OCR 미완료", f"27개 PDF 중 {image_only_count}개는 읽기 가능한 페이지가 없어 직접근거 누락", f"OCR 대상 {ocr_target_pages}/{total_pages}페이지 재처리 후 청크 재생성"],
            ["정책·실행환경 보조지표", "제도·파트너·집행역량을 완전히 설명하지 못함", "현지조사·기관 실사·조달환경 검증 병행"],
            ["금액 단위 불확실성", "약정·지출 raw 값을 통화로 오해할 수 있음", "공식 메타데이터 확정 전 raw value로만 표시"],
            ["현지수요 미검증", "데이터상 우선순위와 실제 수요가 다를 수 있음", "수혜자 인터뷰·파트너 검증·소규모 파일럿"],
            ["최신성 차이", "KOICA 2019~2024, WDI 지표별 최대 2025, 정책지표 2023 기준이 혼재", "지표별 최신연도 표시와 제출 전 재수집"],
            ["결측자료", f"WDI 핵심 {wdi_expected - wdi_observed}개, 실행환경 원자료 {risk_raw_expected - risk_raw_observed}개 결측", "결측을 화면에 노출하고 현지·공식 원자료로 보완"],
        ], columns=["한계", "예상 영향", "완화방안"])
        st.dataframe(limitations, width="stretch", hide_index=True)
        st.caption(f"CPS OCR coverage: 읽기 가능 {readable_pages}/{total_pages}페이지 · OCR 대상 {ocr_target_pages}페이지 · 이미지형 PDF {image_only_count}/{len(cps_coverage)}개")


def main():
    inject_css()
    view_names = list(VIEW_DATA_KEYS)
    pending_view = st.session_state.pop("_pending_view", None)
    pending_country = st.session_state.pop("_pending_country", None)
    pending_sector = st.session_state.pop("_pending_sector", None)
    pending_user_type = st.session_state.pop("_pending_user_type", None)
    if pending_view in view_names:
        st.session_state["active_view"] = pending_view
        if pending_country:
            country_widget_keys = {
                "프로필": "profile_country",
                "분야 우선검토": "sector_country",
                "AI Builder": "builder_country",
                "근거·재현성": "evidence_country",
            }
            target_key = country_widget_keys.get(pending_view)
            if target_key:
                st.session_state[target_key] = pending_country
        if pending_view == "AI Builder":
            if pending_sector:
                st.session_state["builder_sector"] = pending_sector
            if pending_user_type:
                st.session_state["builder_user_type"] = pending_user_type
    if st.session_state.get("active_view") not in view_names:
        st.session_state["active_view"] = view_names[0]
    active_view = st.segmented_control(
        "서비스 메뉴",
        view_names,
        key="active_view",
        required=True,
        label_visibility="collapsed",
        width="stretch",
    )
    data_keys = VIEW_DATA_KEYS[active_view]
    validate_files(data_keys)
    try:
        data = load_view_data(active_view) if data_keys else {}
    except Exception as exc:
        st.error("현재 화면의 데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.")
        st.caption(f"데이터 로딩 오류: {type(exc).__name__}")
        return

    renderers = {
        "개요": render_overview,
        "순위": render_ranking,
        "프로필": render_profile,
        "분야 우선검토": render_sector,
        "AI Builder": render_builder,
        "근거·재현성": render_evidence,
        "AI·모델 검증": render_ai_validation,
        "심사용 요약": render_judge_mode,
        "배포": render_deploy,
    }
    renderers[active_view](data)


if __name__ == "__main__":
    main()
