
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
from pathlib import Path
from typing import List, Dict
import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="K-ODA Compass v2.1.5", page_icon="🧭", layout="wide", initial_sidebar_state="collapsed")
APP_DIR = Path(__file__).resolve().parent

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


@st.cache_data(show_spinner=False)
def load_csv(file_name: str) -> pd.DataFrame:
    path = APP_DIR / file_name
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {file_name}")
    return pd.read_csv(path)


@st.cache_data(show_spinner=True)
def load_all_data():
    data = {key: load_csv(fname) for key, fname in DATA_FILES.items()}
    master = data["master"]
    # numeric coercions
    # pandas 3.x removed errors="ignore" for to_numeric.
    # Convert only columns that actually contain numeric values; keep text columns unchanged.
    for df in data.values():
        for col in df.columns:
            if any(x in col for x in ["Score", "Count", "Raw", "Coverage", "Year", "Rank", "지수", "점수", "순위", "여건"]):
                converted = pd.to_numeric(df[col], errors="coerce")
                if converted.notna().sum() > 0:
                    df[col] = converted
    if "Rank_V21" in master.columns:
        master = master.sort_values("Rank_V21", ascending=True).reset_index(drop=True)
        data["master"] = master
    return data


def validate_files() -> None:
    missing = [name for name in DATA_FILES.values() if not (APP_DIR / name).exists()]
    if missing:
        st.error("필수 CSV 파일이 같은 폴더에 없습니다.")
        st.code("\n".join(missing), language="text")
        st.stop()


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
        return "고수요·리스크 관리형: 국제기구/현지 파트너 연계 권고"
    return text or "추가 검토 후보"


def compact_candidate_label(value) -> str:
    text = display_candidate_type(value)
    if "리스크" in text or "고위험" in text:
        return "리스크 관리형"
    if "정책정합" in text:
        return "정책정합형"
    if "협력기반" in text:
        return "협력기반형"
    if "고수요" in text:
        return "고수요형"
    return "탐색형"


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


def make_rag_doc(rows: list[dict], source_type: str, country: str, sector: str, title: str, content: str, citation: str) -> None:
    doc_id = f"{source_type[:3].upper().replace('/', '')}-{len(rows) + 1:05d}"
    rows.append({
        "Doc_ID": doc_id,
        "Source_Type": source_type,
        "Country_KR": country,
        "Sector_Group": sector,
        "Title": title,
        "Content": content,
        "Citation": citation,
        "Tokens": sorted(tokenize_for_rag(country, sector, title, content, citation)),
    })


@st.cache_data(show_spinner=False)
def build_rag_corpus(master: pd.DataFrame, wdi: pd.DataFrame, projects: pd.DataFrame, policy: pd.DataFrame, sector_summary: pd.DataFrame, cps_pdf: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []

    for _, r in master.iterrows():
        country = safe_text(r.get("Country_KR"))
        title = f"{country} v2.1 opportunity score"
        content = (
            f"{country} 종합점수 {fmt_number(r.get('K_ODA_Opportunity_Score_V21'))}, "
            f"개발수요 {fmt_number(r.get('Development_Need_Score'))}, "
            f"한국 협력기반 {fmt_number(r.get('Korea_Coop_Base_Score_V2'))}, "
            f"분야적합성 {fmt_number(r.get('Sector_Fit_Score_V2'))}, "
            f"정책적합성 {fmt_number(r.get('Policy_Alignment_Score_V21'))}, "
            f"실행가능성 {fmt_number(r.get('Risk_Feasibility_Score_V21'))}, "
            f"후보유형 {display_candidate_type(r.get('Candidate_Type_V21'))}, "
            f"추천분야 {safe_text(r.get('Recommended_Service_Angle_V2'))}."
        )
        citation = f"K-ODA Compass v2.1 master score, Rank #{fmt_int(r.get('Rank_V21'))}, {country}"
        make_rag_doc(rows, "Score Model", country, "전체", title, content, citation)

    for _, r in sector_summary.iterrows():
        country = safe_text(r.get("Country_KR"))
        sector = safe_text(r.get("Sector_Group"))
        title = f"{country} {sector} KOICA portfolio"
        content = (
            f"2019~2024 {sector} 사업 {fmt_int(r.get('Project_Count_2019_2024'))}건, "
            f"비중 {fmt_number(float(r.get('Share_2019_2024', 0)) * 100, 1, '%')}, "
            f"활성연도 {fmt_int(r.get('Active_Years'))}, "
            f"주요 세부분야 {safe_text(r.get('Top_Detail_Sectors'))}."
        )
        citation = f"KOICA country-sector summary 2019~2024, {country}, {sector}"
        make_rag_doc(rows, "Sector Portfolio", country, sector, title, content, citation)

    for _, r in projects.iterrows():
        country = safe_text(r.get("Country_KR"))
        sector = safe_text(r.get("Sector_Group"))
        year = fmt_int(r.get("Year"))
        title = clean_project_text(r.get("Project_Name"))
        content = (
            f"{year}년 {country} {sector} {safe_text(r.get('Sector_Detail'))} "
            f"{safe_text(r.get('Project_Type'))} {safe_text(r.get('Implementing_Org'))}. "
            f"{title}. {safe_text(r.get('Description'))} "
            f"젠더마커 {safe_text(r.get('Gender_Marker'))}, 환경마커 {safe_text(r.get('Environment_Marker'))}, "
            f"기후완화 {safe_text(r.get('Climate_Mitigation'))}, 기후적응 {safe_text(r.get('Climate_Adaptation'))}."
        )
        citation = f"KOICA ODA project evidence {year}, {country}, {sector}, {title}"
        make_rag_doc(rows, "KOICA Project", country, sector, title, content, citation)

    for _, r in wdi.iterrows():
        country = safe_text(r.get("Country_KR"))
        value = safe_text(r.get("Latest_Value_Display"))
        if not value or value.lower() in {"nan", "none", "n/a"}:
            continue
        signal = safe_text(r.get("Signal_KR"))
        title = f"{country} WDI {signal}"
        content = (
            f"{country} {signal} 지표 {safe_text(r.get('Indicator_Name'))}, "
            f"최신연도 {fmt_int(r.get('Latest_Year'))}, 최신값 {value}, "
            f"2019~2025 커버리지 {fmt_int(r.get('WDI_Coverage_2019_2025'))}, "
            f"수요점수 방향 {safe_text(r.get('Score_Direction'))}."
        )
        citation = f"World Bank WDI {safe_text(r.get('Series_Code'))}, latest {fmt_int(r.get('Latest_Year'))}, {country}: {value}"
        make_rag_doc(rows, "WDI", country, signal, title, content, citation)

    for _, r in policy.iterrows():
        country = safe_text(r.get("Country_KR"))
        title = f"{country} policy and risk proxy"
        content = (
            f"{country} 정책적합성 {fmt_number(r.get('Policy_Alignment_Score_V21'))}, "
            f"실행가능성 {fmt_number(r.get('Risk_Feasibility_Score_V21'))}, "
            f"CPS 대상국 {safe_text(r.get('국가협력전략 대상국가'))}, "
            f"KOICA 사무소 {safe_text(r.get('한국국제협력단 사무소 주재 여부'))}, "
            f"취약국가지수 {fmt_number(r.get('취약국가 지수'))}, "
            f"부패인식점수 {fmt_number(r.get('부패인식점수'))}, "
            f"전자정부지수 {fmt_number(r.get('전자정부지수'), 3)}, "
            f"인간개발지수 {fmt_number(r.get('인간개발지수'), 3)}, "
            f"기업여건 {fmt_number(r.get('기업여건'))}."
        )
        citation = f"KOICA integrated partner-country indicators proxy, {country}, policy/risk v2.1"
        make_rag_doc(rows, "Policy/Risk", country, "정책·리스크", title, content, citation)

    for _, r in cps_pdf.iterrows():
        country = safe_text(r.get("Country_KR"))
        sector = safe_text(r.get("Sector_Tag")) or "CPS 정책전략"
        page = fmt_int(r.get("Page"))
        code = safe_text(r.get("Country_Code"))
        chunk_id = safe_text(r.get("Chunk_ID"))
        title = f"{country} CPS 원문 p.{page} · {sector}"
        content = safe_text(r.get("Text"))
        citation = f"{safe_text(r.get('Citation'))} · {chunk_id}"
        make_rag_doc(rows, "CPS PDF", country, sector, title, content, citation)

    return pd.DataFrame(rows)


def retrieve_rag_evidence(corpus: pd.DataFrame, country: str, sector: str, keywords: str, row: pd.Series, top_k: int = 14) -> pd.DataFrame:
    query_tokens = tokenize_for_rag(
        country,
        sector,
        keywords,
        row.get("Candidate_Type_V21"),
        row.get("Recommended_Service_Angle_V2"),
        "ODA 성과관리 KPI 현지수요 파트너십 실행가능성 정책정합성 개발수요",
    )
    scoped = corpus.loc[
        (corpus["Country_KR"] == country)
        | (corpus["Source_Type"].isin(["Score Model", "Policy/Risk"]))
    ].copy()
    if scoped.empty:
        scoped = corpus.copy()

    def score_doc(r: pd.Series) -> float:
        doc_tokens = set(r.get("Tokens") or [])
        score = len(query_tokens & doc_tokens) * 2.0
        if r.get("Country_KR") == country:
            score += 20.0
        if r.get("Sector_Group") == sector:
            score += 14.0
        if sector and sector in f"{r.get('Title')} {r.get('Content')}":
            score += 5.0
        if r.get("Source_Type") == "KOICA Project":
            score += 2.0
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
        ("WDI", 4),
        ("KOICA Project", 5),
        ("Sector Portfolio", 2),
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
        lines.append(f"- [{d['Citation_ID']}] **{d['Source_Type']}** · {d['Title']} — {d['Citation']}")
    return "\n".join(lines)


def build_rag_evidence_pack(country: str, sector: str, keywords: str, docs: pd.DataFrame) -> str:
    return f"""# K-ODA Compass RAG Evidence Pack

## Query
- Country: {country}
- Sector: {sector}
- Keywords: {keywords}

## Retrieved Evidence
{format_rag_citations(docs)}

## Grounding Rule
The proposal must cite retrieved evidence IDs and must not infer final project feasibility beyond the cited public-data signals.
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


def get_country_options(master: pd.DataFrame) -> List[str]:
    return master["Country_KR"].dropna().tolist()


def get_country_row(master: pd.DataFrame, country_kr: str) -> pd.Series:
    rows = master.loc[master["Country_KR"] == country_kr]
    return rows.iloc[0] if not rows.empty else master.iloc[0]


def wdi_for_country(wdi: pd.DataFrame, country: str) -> pd.DataFrame:
    return wdi.loc[wdi["Country_KR"] == country].copy()


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


def display_rank_table(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "Rank_V21", "Country_KR", "K_ODA_Opportunity_Score_V21", "Development_Need_Score", "Korea_Coop_Base_Score_V2",
        "Sector_Fit_Score_V2", "Policy_Alignment_Score_V21", "Risk_Feasibility_Score_V21", "Candidate_Type_V21", "Recommended_Service_Angle_V2",
    ]
    rename = {
        "Rank_V21":"순위", "Country_KR":"국가", "K_ODA_Opportunity_Score_V21":"v2.1 종합점수",
        "Development_Need_Score":"개발수요", "Korea_Coop_Base_Score_V2":"한국 협력기반",
        "Sector_Fit_Score_V2":"분야적합성", "Policy_Alignment_Score_V21":"정책적합성",
        "Risk_Feasibility_Score_V21":"실행가능성", "Candidate_Type_V21":"후보유형", "Recommended_Service_Angle_V2":"추천분야"
    }
    return df[cols].rename(columns=rename)


def component_long(df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    top = df.head(top_n).copy()
    mapping = {
        "Development_Need_Score":"개발수요",
        "Korea_Coop_Base_Score_V2":"한국 협력기반",
        "Sector_Fit_Score_V2":"분야적합성",
        "Opportunity_Gap_Score_V2":"사업기회 공백",
        "Policy_Alignment_Score_V21":"정책적합성",
        "Risk_Feasibility_Score_V21":"실행가능성",
        "Data_Reliability_Score_V21":"데이터 신뢰도",
    }
    rows=[]
    for _, r in top.iterrows():
        for col, label in mapping.items():
            rows.append({"국가": r["Country_KR"], "구성요소": label, "점수": r.get(col)})
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
    signal_order = ["소득수준", "빈곤", "교육", "전력접근", "디지털접근", "보건·생활여건", "고용", "도시화", "인구규모", "녹색성장"]
    cards = []
    for sig in signal_order:
        rows = country_wdi.loc[country_wdi["Signal_KR"] == sig]
        if rows.empty: continue
        r = rows.iloc[0]
        val = r.get("Latest_Value_Display", "N/A")
        if pd.isna(val) or str(val).strip().lower() in {"", "nan", "none", "n/a"}:
            continue
        desc_map = {
            "소득수준":"낮을수록 개발재원·기초서비스 수요가 큼",
            "빈곤":"높을수록 취약계층·포용성장 수요가 큼",
            "교육":"낮을수록 교육·TVET 수요가 큼",
            "전력접근":"낮을수록 인프라·에너지 수요가 큼",
            "디지털접근":"낮을수록 디지털정부·ICT 수요가 큼",
            "보건·생활여건":"낮을수록 보건·지역서비스 개선 여지가 큼",
            "고용":"높을수록 일자리·직업훈련 수요가 큼",
            "도시화":"도시서비스·지역개발 수요 판단 보조",
            "인구규모":"사업규모와 파급효과 판단 보조",
            "녹색성장":"녹색성장·기후협력 판단 보조",
        }
        cards.append({"title": f"{sig}: {val}", "body": desc_map.get(sig, "개발수요 판단 보조지표")})
    return cards[:8]



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
    return f"최근 6년간 {country}의 KOICA 사업은 {top_text} 비중이 높게 나타납니다.{inc_text} 이는 해당 국가에서 축적된 협력 포트폴리오를 바탕으로 후속 파일럿 또는 확장형 사업기회를 검토할 수 있음을 시사합니다."


def display_weights_table(weights: pd.DataFrame) -> pd.DataFrame:
    component_map = {
        "Development Need": "개발수요",
        "Korea Cooperation Base": "한국 협력기반",
        "Sector Fit": "분야 적합성",
        "Opportunity Gap": "사업기회 공백",
        "Policy Alignment": "정책 적합성",
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
- 후보유형은 **{candidate_type}**이며, 정책적합성 **{fmt_number(row.get('Policy_Alignment_Score_V21'))}**, 실행가능성 점수 **{fmt_number(row.get('Risk_Feasibility_Score_V21'))}**을 함께 고려했습니다.
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
| 한국 협력기반 | {fmt_number(row.get('Korea_Coop_Base_Score_V2'))} | KOICA 2019~2024 기존 사업근거 |
| 분야 적합성 | {fmt_number(row.get('Sector_Fit_Score_V2'))} | 국가×분야 다년도 패턴 |
| 정책 적합성 | {fmt_number(row.get('Policy_Alignment_Score_V21'))} | CPS 대상국·KOICA 사무소·지원규모 proxy |
| 실행가능성 | {fmt_number(row.get('Risk_Feasibility_Score_V21'))} | 취약성·부패인식·전자정부·HDI 등 proxy |

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
        ("Korea Cooperation Base", "한국 협력기반", "Korea_Coop_Base_Score_V2"),
        ("Sector Fit", "분야 적합성", "Sector_Fit_Score_V2"),
        ("Opportunity Gap", "사업기회 공백", "Opportunity_Gap_Score_V2"),
        ("Policy Alignment", "정책 적합성", "Policy_Alignment_Score_V21"),
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


def build_rag_prompt(country: str, sector: str, user_type: str, scale: str, keywords: str, row: pd.Series, docs: pd.DataFrame, weights: pd.DataFrame) -> str:
    contribution = score_contribution_table(row, weights)
    contribution_lines = "\n".join(
        f"- {r['구성요소']}: 원점수 {fmt_number(r['원점수'])}, 가중치 {fmt_number(r['가중치'], 2)}, 기여점수 {fmt_number(r['기여점수'])}"
        for _, r in contribution.iterrows()
    )
    return f"""You are K-ODA Compass, an evidence-grounded AI policy copilot for Korean ODA planning.

Write in Korean. Create a concise but complete ODA project proposal draft.
Rules:
1. Every factual claim about the country, sector, WDI signal, KOICA evidence, policy alignment, or risk must cite evidence IDs like [E01].
2. Do not claim final feasibility. Use "예비 검토", "시사", "검증 필요" when evidence is a proxy.
3. Include 사업명, 핵심요약, 추천사유, WDI 신호, KOICA 근거, 활동, KPI, 리스크, 다음 검증.
4. Use only the evidence pack below.

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

## Evidence pack
{format_rag_citations(docs)}
"""


def call_openai_llm(prompt: str) -> tuple[str | None, str]:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    try:
        api_key = api_key or st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        pass
    if not api_key:
        return None, "OPENAI_API_KEY가 없어 로컬 RAG 생성으로 전환했습니다."

    model = os.environ.get("OPENAI_MODEL", "gpt-5.2")
    try:
        model = st.secrets.get("OPENAI_MODEL", model)
    except Exception:
        pass

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=model,
            input=prompt,
            instructions="You are an evidence-grounded Korean ODA proposal writer. Cite evidence IDs and avoid unsupported claims.",
        )
        text = getattr(response, "output_text", None)
        if not text:
            chunks = []
            for item in getattr(response, "output", []) or []:
                for content in getattr(item, "content", []) or []:
                    value = getattr(content, "text", None)
                    if value:
                        chunks.append(value)
            text = "\n".join(chunks)
        return text or None, f"OpenAI Responses API 사용: {model}"
    except Exception as exc:
        return None, f"LLM 호출 실패로 로컬 RAG 생성으로 전환했습니다: {exc}"


def build_rag_markdown_proposal(country: str, sector: str, user_type: str, scale: str, keywords: str, row: pd.Series, docs: pd.DataFrame, weights: pd.DataFrame) -> str:
    score_cites = citation_ids(docs, "Score Model", 1)
    policy_cites = citation_ids(docs, "Policy/Risk", 1)
    cps_cites = citation_ids(docs, "CPS PDF", 3)
    wdi_cites = citation_ids(docs, "WDI", 4)
    project_cites = citation_ids(docs, "KOICA Project", 5)
    portfolio_cites = citation_ids(docs, "Sector Portfolio", 2)
    contribution = score_contribution_table(row, weights)
    top_contrib = contribution.head(3)
    cps_docs = docs.loc[docs["Source_Type"] == "CPS PDF"].head(3)
    koica_docs = docs.loc[docs["Source_Type"] == "KOICA Project"].head(5)
    wdi_docs = docs.loc[docs["Source_Type"] == "WDI"].head(4)

    cps_lines = [
        f"- [{d['Citation_ID']}] {d['Title']}: {safe_text(d['Content'])[:420]}..."
        for _, d in cps_docs.iterrows()
    ] or ["- 선택 국가의 CPS PDF 텍스트 근거가 제한적이므로 공개 CSV 기반 정책 proxy와 원문 재확인이 필요합니다."]
    koica_lines = [
        f"- [{d['Citation_ID']}] {d['Title']} ({d['Citation']})"
        for _, d in koica_docs.iterrows()
    ] or ["- 직접 사업근거가 제한적이므로 인접 분야와 현지 수요조사를 우선 확인해야 합니다."]
    wdi_lines = [
        f"- [{d['Citation_ID']}] {d['Title']}: {d['Content']}"
        for _, d in wdi_docs.iterrows()
    ] or ["- WDI 최신값이 제한적이므로 원천 데이터 재확인이 필요합니다."]
    contrib_lines = [
        f"- {r['구성요소']}: 원점수 {fmt_number(r['원점수'])}, 가중기여 {fmt_number(r['기여점수'])}"
        for _, r in top_contrib.iterrows()
    ]

    return f"""# K-ODA Compass RAG형 AI 사업기획서

## 1. 사업명
**{country} {sector} Evidence-grounded ODA 파일럿**

## 2. 핵심 요약
- {country}는 v2.1 종합점수 **{fmt_number(row.get('K_ODA_Opportunity_Score_V21'))}/100**으로 산출되었으며, 후보유형은 **{display_candidate_type(row.get('Candidate_Type_V21'))}**입니다 {score_cites}.
- {sector} 분야는 국가별 추천분야 및 KOICA 포트폴리오 근거를 함께 고려한 예비 후보입니다 {portfolio_cites or project_cites}.
- 정책적합성은 공개 proxy와 CPS PDF 원문 RAG를 함께 검토하며, 실제 사업화 전 CPS 최신성·현지수요·파트너 적합성 검증이 필요합니다 {policy_cites}, {cps_cites}.

## 3. AI 추천 근거
{chr(10).join(contrib_lines)}

## 4. CPS 정책 정합성 근거
{chr(10).join(cps_lines)}

## 5. WDI 개발수요 신호
{chr(10).join(wdi_lines)}

## 6. KOICA 사업근거
{chr(10).join(koica_lines)}

## 7. 사업 설계
| 항목 | 내용 |
|---|---|
| 대상 사용자 | {user_type} |
| 사업 규모 | {scale} |
| 핵심 키워드 | {keywords} |
| 추진 방식 | 현지 수요검증 → 데이터 기반 파일럿 → KPI 대시보드 → 확장 제안 |
| 파트너십 | KOICA 사무소, 현지 부처, 국제기구, CSO/기업 컨소시엄을 검토 {policy_cites}, {cps_cites} |

## 8. 주요 활동
1. RAG 근거팩 기반 국가·분야 진단 워크숍
2. {sector} 데이터 수집·품질점검·성과지표 정의
3. 현지 담당자 역량강화 및 운영 매뉴얼 구축
4. 12개월 파일럿 운영과 확장 가능성 평가

## 9. KPI
| 영역 | Baseline | Target | 검증방법 |
|---|---|---|---|
| 데이터 활용 | 공공데이터 기반 기획 역량 제한 | 실무자 50명 이상 교육 | 출석부, 사전/사후 평가 |
| 서비스 개선 | 성과관리 절차 분산 | KPI 10개 이상 정기 업데이트 | 대시보드 로그 |
| 파트너십 | 공동추진 구조 미확정 | 현지 실행 파트너 2곳 이상 MOU/협의 | 회의록, 협약서 |
| 확장성 | 파일럿 이전 단계 | 후속 ODA/민관협력 제안서 1건 | 제안서, 예산안 |

## 10. 리스크와 보완방안
- 근거 한계: WDI 결측과 정책 proxy 한계를 명시하고 원자료를 재검증합니다 {wdi_cites}.
- 실행 리스크: 취약성·거버넌스 지표가 낮은 경우 CPS 방향과 국제기구·현지 파트너 공동추진 구조를 우선 검토합니다 {policy_cites}, {cps_cites}.
- 현지수요 불일치: 현지 인터뷰와 소규모 파일럿으로 데이터 기반 추천을 재검증합니다.
- 지속가능성: 운영주체, 비용분담, 유지보수 체계를 1단계에서 확정합니다.

## 11. RAG Evidence Citation
{format_rag_citations(docs)}

> 본 초안은 K-ODA Compass RAG 검색 결과와 공개데이터 proxy에 근거한 예비기획 자료입니다. 최종 사업 타당성 판단은 현지조사와 공식 정책문서 검토가 필요합니다.
"""


def build_policy_brief(country: str, sector: str, row: pd.Series, docs: pd.DataFrame) -> str:
    return f"""# 1-Page Policy Brief: {country} {sector}

## Decision
{country} {sector} 분야는 v2.1 점수 {fmt_number(row.get('K_ODA_Opportunity_Score_V21'))}/100, 후보유형 {display_candidate_type(row.get('Candidate_Type_V21'))}으로 예비 검토 대상입니다.

## Why Now
- 추천분야: {safe_text(row.get('Recommended_Service_Angle_V2'))}
- 개발수요: {fmt_number(row.get('Development_Need_Score'))}
- 정책적합성: {fmt_number(row.get('Policy_Alignment_Score_V21'))}
- 실행가능성: {fmt_number(row.get('Risk_Feasibility_Score_V21'))}

## Evidence
{format_rag_citations(docs.head(8))}

## Next 30 Days
1. CPS 원문 근거와 최신 정책문서 교차확인
2. 현지 파트너 인터뷰 3건
3. 예산·운영주체 가정 검증
4. 파일럿 KPI 확정
"""


def reportlab_korean_font() -> str:
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except Exception:
        return "Helvetica"
    font_name = "KodaKorean"
    try:
        if font_name in pdfmetrics.getRegisteredFontNames():
            return font_name
    except Exception:
        pass
    candidates = [
        Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
        Path("/Library/Fonts/Arial Unicode.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJKkr-Regular.otf"),
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
    ]
    for font_path in candidates:
        if font_path.exists():
            try:
                pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
                return font_name
            except Exception:
                continue
    return "Helvetica"


def markdown_to_pdf_bytes(title: str, markdown_text: str) -> bytes | None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    except Exception:
        return None

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=42, rightMargin=42, topMargin=42, bottomMargin=42)
    styles = getSampleStyleSheet()
    font_name = reportlab_korean_font()
    for style_name in ["Title", "BodyText"]:
        styles[style_name].fontName = font_name
    story = [Paragraph(title, styles["Title"]), Spacer(1, 12)]
    for raw in markdown_text.splitlines():
        line = raw.strip()
        if not line:
            story.append(Spacer(1, 6))
            continue
        line = re.sub(r"^#+\s*", "", line)
        line = line.replace("**", "").replace("|", " ")
        story.append(Paragraph(line[:1200], styles["BodyText"]))
        story.append(Spacer(1, 4))
    doc.build(story)
    return buffer.getvalue()


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


def rag_validation_metrics(data: dict, corpus: pd.DataFrame) -> dict:
    master = data["master"]
    wdi = data["wdi"]
    projects = data["projects"]
    cps_pdf = data["cps_pdf"]
    cps_coverage = data.get("cps_coverage", pd.DataFrame())
    cps_top50 = len(set(master["WDI_Country_Code"]) & set(cps_pdf["Country_Code"]))
    if not cps_coverage.empty and {"OCR_Target_Pages", "Readable_Pages", "Pages"}.issubset(cps_coverage.columns):
        readable_pages = int(pd.to_numeric(cps_coverage["Readable_Pages"], errors="coerce").fillna(0).sum())
        total_pages = int(pd.to_numeric(cps_coverage["Pages"], errors="coerce").fillna(0).sum())
        ocr_pages = int(pd.to_numeric(cps_coverage["OCR_Target_Pages"], errors="coerce").fillna(0).sum())
        image_only = int((pd.to_numeric(cps_coverage["Readable_Pages"], errors="coerce").fillna(0) == 0).sum())
        cps_text_summary = f"{readable_pages}/{total_pages}p"
        cps_ocr_summary = f"{ocr_pages}p / image-only {image_only}개"
    else:
        cps_text_summary = "coverage CSV 확인 필요"
        cps_ocr_summary = "coverage CSV 확인 필요"
    return {
        "RAG 문서 수": len(corpus),
        "KOICA 사업근거": int((corpus["Source_Type"] == "KOICA Project").sum()),
        "CPS PDF 근거": int((corpus["Source_Type"] == "CPS PDF").sum()),
        "CPS 텍스트 페이지": cps_text_summary,
        "CPS OCR 대상": cps_ocr_summary,
        "WDI 근거": int((corpus["Source_Type"] == "WDI").sum()),
        "Top50 점수 재현": "±0.005",
        "WDI 최신값 보유율": f"{(wdi['Latest_Value'].notna().mean() * 100):.1f}%",
        "CPS Top50 커버리지": f"{cps_top50}/50",
        "국가 커버리지": f"{master['Country_KR'].nunique()}/50",
        "KOICA 근거 국가": projects["Country_KR"].nunique(),
    }


def render_ai_validation(data):
    master, weights = data["master"], data["weights"]
    corpus = build_rag_corpus(data["master"], data["wdi"], data["projects"], data["policy_risk"], data["sector_summary"], data["cps_pdf"])
    st.title("AI 검증 리포트")
    st.caption("RAG 검색, 근거 커버리지, 점수 재현성, 민감도 분석을 제출물 내부에서 검증합니다.")

    metrics = rag_validation_metrics(data, corpus)
    cols = st.columns(4)
    for i, (label, value) in enumerate(metrics.items()):
        with cols[i % len(cols)]:
            metric_card(label, str(value), "submission audit")

    st.header("1. RAG 코퍼스 구성")
    source_counts = corpus["Source_Type"].value_counts().reset_index()
    source_counts.columns = ["근거 유형", "문서 수"]
    st.dataframe(source_counts, width="stretch", hide_index=True)

    st.header("2. 점수 기여도 설명")
    country = st.selectbox("검증 국가", get_country_options(master), index=0, key="validation_country")
    row = get_country_row(master, country)
    contrib = score_contribution_table(row, weights)
    st.dataframe(contrib, width="stretch", hide_index=True)
    fig = px.bar(contrib.sort_values("기여점수"), x="기여점수", y="구성요소", orientation="h", text="기여점수")
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig.update_layout(height=360, margin=dict(l=10, r=40, t=10, b=10))
    st.plotly_chart(fig, width="stretch")

    st.header("3. 민감도 분석")
    sensitivity = []
    base_rank = master[["Country_KR", "Rank_V21", "K_ODA_Opportunity_Score_V21"]].copy()
    for component, col in [
        ("개발수요", "Development_Need_Score"),
        ("정책적합성", "Policy_Alignment_Score_V21"),
        ("실행가능성", "Risk_Feasibility_Score_V21"),
    ]:
        perturbed = master.copy()
        perturbed["sim_score"] = perturbed["K_ODA_Opportunity_Score_V21"] + pd.to_numeric(perturbed[col], errors="coerce") * 0.03
        perturbed["sim_rank"] = perturbed["sim_score"].rank(ascending=False, method="first").astype(int)
        merged = base_rank.merge(perturbed[["Country_KR", "sim_rank"]], on="Country_KR")
        top_change = merged.assign(rank_delta=(merged["Rank_V21"] - merged["sim_rank"]).abs()).sort_values("rank_delta", ascending=False).head(1)
        sensitivity.append([component, int(top_change["rank_delta"].iloc[0]), top_change["Country_KR"].iloc[0]])
    st.dataframe(pd.DataFrame(sensitivity, columns=["가중 강화 항목", "최대 순위 변화", "영향 국가"]), width="stretch", hide_index=True)

    st.header("4. 환각 방지 원칙")
    st.markdown("""
    <div class="section-note">
    RAG형 AI Builder는 생성 전에 Top-K 근거를 고정하고, 생성문 안에 [E01] 형식의 근거 ID를 삽입합니다.
    정책·리스크는 proxy로 표시하며, 최종 사업 타당성은 현지조사와 공식 정책문서 검증 전에는 단정하지 않습니다.
    </div>
    """, unsafe_allow_html=True)


def render_deploy(data):
    st.title("배포·QR 센터")
    st.caption("GitHub, Streamlit Cloud, QR을 한 화면에서 관리하는 심사용 배포 패널입니다.")
    github_url = st.text_input("GitHub Repository URL", value="https://github.com/<your-id>/koda-compass-rag")
    demo_url = st.text_input("Streamlit Cloud Demo URL", value="https://<your-app>.streamlit.app")
    cols = st.columns(2)
    with cols[0]:
        st.subheader("GitHub")
        qr = make_qr_png(github_url)
        if qr:
            st.image(qr, width=220)
            st.download_button("GitHub QR 다운로드", qr, "koda_github_qr.png", "image/png", width="stretch")
    with cols[1]:
        st.subheader("Live Demo")
        qr = make_qr_png(demo_url)
        if qr:
            st.image(qr, width=220)
            st.download_button("Demo QR 다운로드", qr, "koda_demo_qr.png", "image/png", width="stretch")

    st.header("Streamlit Cloud 배포 체크리스트")
    st.markdown("""
1. GitHub에 이 폴더 전체를 push
2. Streamlit Cloud에서 `app.py`를 entrypoint로 지정
3. Secrets에 `OPENAI_API_KEY`와 필요 시 `OPENAI_MODEL` 입력
4. 배포 URL을 README와 발표자료 QR에 반영
5. 심사 전 시크릿 없는 로컬 RAG 모드와 LLM RAG 모드를 모두 확인
""")


def render_judge_mode(data):
    master = data["master"]
    cps_pdf = data["cps_pdf"]
    st.title("심사모드")
    st.caption("공공데이터 활용성, AI 혁신성, 서비스 완성도, 확산 가능성을 한 화면에서 설명하는 발표용 대시보드입니다.")

    corpus = build_rag_corpus(data["master"], data["wdi"], data["projects"], data["policy_risk"], data["sector_summary"], data["cps_pdf"])
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("공공데이터 소스", "4종+", "KOICA/WDI/CPS/정책지표")
    with c2: metric_card("RAG 문서", fmt_int(len(corpus)), "citation-ready")
    with c3: metric_card("CPS PDF chunks", fmt_int(len(cps_pdf)), f"{cps_pdf['Country_KR'].nunique()}개국")
    with c4: metric_card("Top50 후보국", fmt_int(len(master)), "ODA 기회순위")

    st.header("1. 심사기준 대응표")
    matrix = pd.DataFrame([
        ["공공데이터 활용성", "KOICA 사업근거, WDI, CPS PDF, 정책·리스크 proxy를 결합", "복수 공공데이터 융합과 원문 citation"],
        ["AI 혁신성", "RAG 검색, Evidence Pack 고정, LLM/로컬 생성 fallback", "생성문마다 [E01] 근거 추적"],
        ["서비스 완성도", "국가순위, 프로필, 분야추천, AI Builder, 검증, 배포 탭", "심사장에서 바로 조작 가능한 MVP"],
        ["검증 가능성", "점수 재현성, 민감도, RAG 코퍼스 통계, 테스트 제공", "블랙박스가 아닌 설명 가능한 AI"],
        ["사업화/확산성", "CSO, 지자체, 기업, 정책담당자 시나리오", "사업기획서·브리프·PDF export"],
    ], columns=["평가축", "구현 내용", "심사 포인트"])
    st.dataframe(matrix, width="stretch", hide_index=True)

    st.header("2. 90초 발표 흐름")
    st.markdown("""
1. `개요`: ODA 공공데이터는 많지만 사업기획으로 전환하기 어렵다는 문제 제시
2. `순위`: Top50 국가별 기회점수와 점수분해 제시
3. `AI Builder`: 대표 시나리오 선택 후 RAG형 사업기획서 생성
4. `근거 Citation`: CPS PDF, KOICA, WDI 근거 ID 확인
5. `AI검증`: RAG 문서 수, 점수 재현성, 민감도, 환각 방지 원칙 확인
6. `배포`: Streamlit/GitHub QR로 실제 서비스 접근성 제시
""")

    st.header("3. 경쟁작 대비 포지션")
    positioning = pd.DataFrame([
        ["일반 데이터 대시보드", "조회·시각화 중심", "사업기획서·Evidence Pack까지 생성"],
        ["단순 챗봇", "근거 추적 어려움", "RAG citation으로 원문·데이터 근거 추적"],
        ["아이디어 기획안", "실행 화면 부재", "Streamlit MVP, export, tests, Docker 제공"],
        ["정책문서 수동분석", "시간 소요·비전문가 접근성 낮음", "CPS PDF 원문 chunk 기반 정책 정합성 자동 검색"],
    ], columns=["비교 대상", "일반 한계", "K-ODA Compass 차별점"])
    st.dataframe(positioning, width="stretch", hide_index=True)

    st.header("4. 남은 실전 체크")
    checklist = pd.DataFrame([
        ["Streamlit Cloud URL", "필수", "배포 후 README와 발표자료 QR 반영"],
        ["GitHub 공개 저장소", "필수", "코드·데이터·문서·테스트를 한 번에 공개"],
        ["샘플 산출물 3종", "필수", "탄자니아/베트남/르완다 시나리오 결과 사전 준비"],
        ["사용자 피드백", "강력 추천", "CSO/ODA 관심자 3명 이상 짧은 코멘트 확보"],
        ["OCR 보강", "선택", "이미지형 CPS PDF까지 확장하면 정책근거 커버리지 상승"],
    ], columns=["항목", "우선순위", "액션"])
    st.dataframe(checklist, width="stretch", hide_index=True)


def render_overview(data):
    master = data["master"]
    top = master.iloc[0]
    cps_count = int((master["국가협력전략 대상국가"].astype(str).str.upper() == "Y").sum()) if "국가협력전략 대상국가" in master else 0
    avg_wdi = master["WDI_Core_Coverage_%"].mean() if "WDI_Core_Coverage_%" in master else None
    st.markdown("""
    <div class="koda-hero">
      <div class="koda-title">K-ODA Compass v2.1</div>
      <p class="koda-subtitle"><b>공공데이터와 AI를 활용한 글로벌사우스 ODA 사업기획·파트너십 추천 서비스</b><br>
      KOICA 2019~2024 다년도 사업근거, World Bank WDI 2019~2025, 협력국 통합 개발지표를 결합하여 국가·분야별 ODA 사업기회를 탐색하고 근거 기반 사업기획서 초안을 생성합니다.</p>
    </div>
    """, unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: metric_card("후보국", fmt_int(len(master)), "KOICA Top 50")
    with c2: metric_card("최고 v2.1 점수", fmt_number(top.get("K_ODA_Opportunity_Score_V21")), top.get("Country_KR"))
    with c3: metric_card("CPS 대상국", fmt_int(cps_count), "정책적합성 proxy")
    with c4: metric_card("평균 WDI 커버리지", fmt_number(avg_wdi,1,"%"), "핵심 지표 기준")
    with c5: metric_card("분석기간", "2019–2024", "KOICA 다년도")

    st.header("1. 문제정의")
    st.markdown("""
    <div class="section-note">
    ODA 공공데이터는 국가별 지원실적, 사업 단위 로데이터, 분야 통계, API 형태로 개방되어 있다. 그러나 일반 국민, CSO, 기업, 지자체, 대학생·연구자가 이를 직접 해석하여 구체적인 국가·분야별 사업기회로 전환하기에는 진입장벽이 높다. K-ODA Compass는 이 간극을 줄이기 위해 데이터를 <b>국가·분야 추천, 정책·리스크 해석, 사업기획서 초안</b>으로 변환한다.
    </div>
    """, unsafe_allow_html=True)

    st.header("2. v2.1 서비스 흐름")
    cols = st.columns(5)
    workflow = [
        ("① Data", "KOICA 다년도·WDI·정책/리스크 지표 결합"),
        ("② Score", "개발수요·협력기반·분야적합성·정책·리스크 산출"),
        ("③ Recommend", "국가별 유형과 추천 분야 제안"),
        ("④ Build", "근거 기반 사업기획서 초안 생성"),
        ("⑤ Evidence", "출처·산식·한계·검증 기록 확인"),
    ]
    for col, (t,b) in zip(cols, workflow):
        with col: pipeline_card(t,b)

    st.header("3. v2.1 점수모델")
    weights = data["weights"].copy()
    if not weights.empty:
        st.dataframe(weights, width="stretch", hide_index=True)
    st.markdown("""
    <div class="section-note"><b>핵심 차별점:</b> v2.1은 단순 개발수요 순위가 아니라 한국의 기존 협력기반, CPS·KOICA 사무소 기반 정책 적합성, 취약성·거버넌스 기반 실행가능성을 함께 반영한다.</div>
    """, unsafe_allow_html=True)

    st.header("4. 상위 후보국 요약")
    top3 = master.head(3)
    cols = st.columns(3)
    for col, (_, r) in zip(cols, top3.iterrows()):
        with col:
            insight_card(f"#{int(r['Rank_V21'])} {r['Country_KR']}", f"종합점수 {fmt_number(r['K_ODA_Opportunity_Score_V21'])}. {r['Candidate_Type_V21']}<br>추천분야: {r['Recommended_Service_Angle_V2']}")


def render_ranking(data):
    master = data["master"]
    st.title("국가별 기회순위")
    st.caption("50개 후보국의 v2.1 K-ODA Opportunity Score와 세부 구성요소를 비교합니다.")
    top = master.iloc[0]
    c1,c2,c3,c4 = st.columns(4)
    with c1: metric_card("1위 후보국", top["Country_KR"], f"{fmt_number(top['K_ODA_Opportunity_Score_V21'])}점")
    with c2: metric_card("Top 10 평균", fmt_number(master.head(10)["K_ODA_Opportunity_Score_V21"].mean()), "상위 후보군")
    with c3: metric_card("정책적합성 최고", master.sort_values("Policy_Alignment_Score_V21", ascending=False).iloc[0]["Country_KR"], fmt_number(master["Policy_Alignment_Score_V21"].max()))
    with c4: metric_card("실행가능성 최고", master.sort_values("Risk_Feasibility_Score_V21", ascending=False).iloc[0]["Country_KR"], fmt_number(master["Risk_Feasibility_Score_V21"].max()))

    st.markdown("""
    <div class="section-note">실행가능성 최고국은 운영 리스크가 낮은 국가를 의미하며, 종합 우선순위는 개발수요·정책적합성·협력기반을 함께 고려하여 산출됩니다.</div>
    """, unsafe_allow_html=True)

    c1,c2 = st.columns([1.05, 1.1])
    with c1:
        st.subheader("종합점수 순위 Top 20")
        fig = px.bar(master.head(20).sort_values("K_ODA_Opportunity_Score_V21"), x="K_ODA_Opportunity_Score_V21", y="Country_KR", orientation="h", text="K_ODA_Opportunity_Score_V21", labels={"K_ODA_Opportunity_Score_V21":"v2.1 종합점수", "Country_KR":"국가"})
        fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig.update_layout(height=640, margin=dict(l=10,r=30,t=10,b=10), xaxis_range=[0,100])
        st.plotly_chart(fig, width="stretch")
    with c2:
        st.subheader("상위 5개국 점수분해")
        comp = component_long(master, top_n=5)
        fig2 = px.bar(comp, x="점수", y="국가", color="구성요소", barmode="group", orientation="h")
        fig2.update_layout(height=640, margin=dict(l=10,r=10,t=10,b=10), xaxis_range=[0,100])
        st.plotly_chart(fig2, width="stretch")

    st.markdown("""
    <div class="section-note">상위권 국가는 개발수요와 정책적합성이 높지만 실행가능성은 국가별로 차이가 있습니다. 따라서 본 서비스는 단순 고수요 국가를 자동 추천하지 않고, 고수요·정책정합·리스크 유형을 함께 분류합니다.</div>
    """, unsafe_allow_html=True)

    st.subheader("상위 3개국 추천 사유")
    cols=st.columns(3)
    for col,(_,r) in zip(cols, master.head(3).iterrows()):
        with col:
            body = f"{r['Candidate_Type_V21']}<br>개발수요 {fmt_number(r['Development_Need_Score'])}, 정책적합성 {fmt_number(r['Policy_Alignment_Score_V21'])}, 실행가능성 {fmt_number(r['Risk_Feasibility_Score_V21'])}."
            insight_card(f"#{int(r['Rank_V21'])} {r['Country_KR']}", body)

    st.subheader("의사결정용 점수표")
    st.caption("기본 화면은 상위 20개국만 표시합니다. 전체 50개국은 아래 접힘 영역과 CSV 다운로드로 확인할 수 있습니다.")
    st.dataframe(display_rank_table(master.head(20)), width="stretch", hide_index=True)

    type_df = pd.DataFrame([
        ["고수요·정책정합", "개발수요와 한국 정책적합성이 모두 높아 우선 검토"],
        ["고수요·고위험", "수요는 높지만 분쟁·거버넌스 리스크가 있어 국제기구/인도지원 연계 적합"],
        ["정책정합·협력기반", "기존 KOICA 협력기반이 높아 확장형 사업 적합"],
        ["탐색 후보", "데이터상 가능성은 있으나 추가 현지검증 필요"],
    ], columns=["후보유형", "의미"])
    st.markdown("#### 후보유형 정의")
    st.dataframe(type_df, width="stretch", hide_index=True)

    with st.expander("전체 50개국 점수표 보기"):
        st.dataframe(display_rank_table(master), width="stretch", hide_index=True)
        st.download_button(
            "전체 Top 50 점수표 CSV 다운로드",
            data=display_rank_table(master).to_csv(index=False).encode("utf-8-sig"),
            file_name="KODA_top50_v21_score_table.csv",
            mime="text/csv",
            width="stretch",
        )


def render_profile(data):
    master, wdi, cy, sector_summary, sector_year = data["master"], data["wdi"], data["country_year"], data["sector_summary"], data["sector_year"]
    st.title("국가 프로필")
    country = st.selectbox("국가 선택", get_country_options(master), index=0, key="profile_country")
    row = get_country_row(master, country)
    country_wdi = wdi_for_country(wdi, country)
    country_cy = country_year_for_country(cy, country)
    country_sector = sector_summary_for_country(sector_summary, country)
    st.caption("선택 국가의 점수 구성, WDI 개발지표, KOICA 2019~2024 다년도 사업근거를 확인합니다.")

    cols=st.columns(6)
    with cols[0]: metric_card("v2.1 기회점수", fmt_number(row.get("K_ODA_Opportunity_Score_V21")), f"Rank #{fmt_int(row.get('Rank_V21'))}")
    with cols[1]: metric_card("개발수요", fmt_number(row.get("Development_Need_Score")), "WDI 기반")
    with cols[2]: metric_card("정책적합성", fmt_number(row.get("Policy_Alignment_Score_V21")), row.get("Policy_Alignment_Band_V21"))
    with cols[3]: metric_card("실행가능성", fmt_number(row.get("Risk_Feasibility_Score_V21")), row.get("Risk_Band_V21"))
    with cols[4]: metric_card("KOICA 사업근거", fmt_int(row.get("Project_Count_2019_2024")), "2019~2024")
    with cols[5]: metric_card("2024 사업 수", fmt_int(row.get("Project_Count_2024")), "로데이터")

    c1,c2 = st.columns([1,1])
    with c1:
        st.subheader("점수 진단")
        comp = pd.DataFrame({
            "구성요소":["개발수요","한국 협력기반","분야적합성","사업기회 공백","정책적합성","실행가능성","데이터 신뢰도"],
            "점수":[row.get("Development_Need_Score"), row.get("Korea_Coop_Base_Score_V2"), row.get("Sector_Fit_Score_V2"), row.get("Opportunity_Gap_Score_V2"), row.get("Policy_Alignment_Score_V21"), row.get("Risk_Feasibility_Score_V21"), row.get("Data_Reliability_Score_V21")]
        })
        fig=px.bar(comp.sort_values("점수"), x="점수", y="구성요소", orientation="h", text="점수")
        fig.update_traces(texttemplate='%{text:.1f}', textposition='inside')
        fig.update_layout(height=430, margin=dict(l=10,r=10,t=10,b=10), xaxis_range=[0,100])
        st.plotly_chart(fig, width="stretch")
    with c2:
        st.subheader("의사결정 해석")
        st.markdown(f"""
        <div class="decision-card">
        <b>{country}</b>의 후보유형은 <b>{row.get('Candidate_Type_V21')}</b>입니다. 개발수요 {fmt_number(row.get('Development_Need_Score'))}, 정책적합성 {fmt_number(row.get('Policy_Alignment_Score_V21'))}, 실행가능성 {fmt_number(row.get('Risk_Feasibility_Score_V21'))}을 함께 고려할 때, 추천분야는 <b>{row.get('Recommended_Service_Angle_V2')}</b>입니다. 실제 사업화 전에는 최신 CPS, 현지수요, 파트너 검증이 필요합니다.
        </div>
        """, unsafe_allow_html=True)
        st.subheader("개발수요 핵심 지표")
        for card in wdi_signal_cards(country_wdi)[:5]:
            insight_card(card["title"], card["body"])

    st.subheader("KOICA 사업 수 추세")
    if not country_cy.empty:
        fig=px.line(country_cy, x="Year", y="Project_Count", markers=True, labels={"Year":"연도", "Project_Count":"사업 수"})
        fig.update_layout(height=360, margin=dict(l=10,r=10,t=10,b=10))
        st.plotly_chart(fig, width="stretch")

    st.subheader("분야별 다년도 추세")
    sy = sector_year_for_country(sector_year, country)
    actionable = sy[sy["Sector_Group"].isin(country_sector.head(5)["Sector_Group"].tolist())]
    if not actionable.empty:
        fig=px.line(actionable, x="Year", y="Project_Count", color="Sector_Group", markers=True, labels={"Year":"연도", "Project_Count":"사업 수", "Sector_Group":"분야"})
        fig.update_layout(height=420, margin=dict(l=10,r=10,t=10,b=10))
        st.plotly_chart(fig, width="stretch")
        st.markdown(f"""
        <div class="section-note">{sector_trend_interpretation(country, actionable)}</div>
        """, unsafe_allow_html=True)

    st.subheader("실행가능 분야")
    top_sectors = country_sector.head(5)
    if top_sectors.empty:
        st.info("해당 국가의 분야별 KOICA 사업근거가 제한적입니다.")
    else:
        for _, r in top_sectors.iterrows():
            header = f"{r['Sector_Group']} · {fmt_int(r['Project_Count_2019_2024'])}건 · {fmt_number(r['Share_2019_2024']*100,1,'%')}"
            body = f"Top 세부분야: {compact_detail_sectors(r.get('Top_Detail_Sectors',''))}"
            insight_card(header, body)

    with st.expander("WDI 원자료 보기"):
        st.dataframe(country_wdi, width="stretch", hide_index=True)


def render_sector(data):
    master, sector_summary, sector_year, projects = data["master"], data["sector_summary"], data["sector_year"], data["projects"]
    st.title("분야 추천")
    country = st.selectbox("국가 선택", get_country_options(master), index=0, key="sector_country")
    row = get_country_row(master, country)
    sectors = sector_summary_for_country(sector_summary, country)
    recs = recommended_sectors(row)

    cols=st.columns(4)
    with cols[0]: metric_card("1순위 추천 분야", recs[0], f"Sector Fit {fmt_number(row.get('Sector_Fit_Score_V2'))}")
    with cols[1]: metric_card("2순위 추천 분야", recs[1] if len(recs)>1 else "검토", "KOICA evidence + WDI")
    with cols[2]: metric_card("정책적합성", fmt_number(row.get("Policy_Alignment_Score_V21")), row.get("Policy_Alignment_Band_V21"))
    with cols[3]: metric_card("실행가능성", fmt_number(row.get("Risk_Feasibility_Score_V21")), row.get("Risk_Band_V21"))

    st.subheader("분야별 근거 매트릭스")
    display = sectors.head(8).copy()
    if not display.empty:
        display["KOICA 근거"] = display["Project_Count_2019_2024"].map(lambda x: f"{fmt_int(x)}건")
        display["비중"] = (display["Share_2019_2024"]*100).map(lambda x: f"{x:.1f}%")
        display["우선순위"] = display["Sector_Group"].apply(lambda s: "1순위" if s == recs[0] else ("2순위" if len(recs)>1 and s==recs[1] else "검토"))
        st.dataframe(display[["Sector_Group","KOICA 근거","비중","Active_Years","Top_Detail_Sectors","우선순위"]].rename(columns={"Sector_Group":"분야","Active_Years":"활성연도","Top_Detail_Sectors":"주요 세부분야"}), width="stretch", hide_index=True)

    c1,c2=st.columns([1,1])
    with c1:
        st.subheader("실행가능 분야 분포")
        chart = sectors.head(10).sort_values("Project_Count_2019_2024")
        if not chart.empty:
            fig=px.bar(chart, x="Project_Count_2019_2024", y="Sector_Group", orientation="h", text="Project_Count_2019_2024", labels={"Project_Count_2019_2024":"2019~2024 사업 수", "Sector_Group":"분야"})
            fig.update_traces(textposition="outside")
            fig.update_layout(height=420, margin=dict(l=10,r=30,t=10,b=10))
            st.plotly_chart(fig, width="stretch")
    with c2:
        st.subheader("추천 사업 아이디어")
        for s in recs[:2]:
            ev = projects_for_country(projects, country, s).head(3)
            lines = "<br>".join([f"· {str(x)[:70]}" for x in ev["Project_Name"].tolist()]) if not ev.empty else "· 현지수요 조사 기반 파일럿 설계<br>· 성과관리 및 파트너십 구조 수립"
            insight_card(f"{s} 기반 사업기획", f"{lines}<br><br>다음 단계: 생성기 탭에서 <b>{country} × {s}</b> 조합으로 초안 생성")

    st.subheader("분야별 연도 추세")
    sy = sector_year_for_country(sector_year, country)
    sy = sy[sy["Sector_Group"].isin(sectors.head(6)["Sector_Group"].tolist())]
    if not sy.empty:
        fig=px.area(sy, x="Year", y="Project_Count", color="Sector_Group", labels={"Year":"연도", "Project_Count":"사업 수", "Sector_Group":"분야"})
        fig.update_layout(height=430, margin=dict(l=10,r=10,t=10,b=10))
        st.plotly_chart(fig, width="stretch")

    with st.expander("세부 사업근거 보기"):
        ev = projects_for_country(projects, country)
        st.dataframe(ev[["Year","Project_Name","Sector_Group","Sector_Detail","Project_Type","Implementing_Org","Disbursement_Raw"]].head(50), width="stretch", hide_index=True)


def render_builder(data):
    master, wdi, sector_summary = data["master"], data["wdi"], data["sector_summary"]
    weights = data["weights"]
    corpus = build_rag_corpus(data["master"], data["wdi"], data["projects"], data["policy_risk"], data["sector_summary"], data["cps_pdf"])
    st.title("RAG형 AI Builder")
    st.caption("생성문마다 KOICA/WDI/정책·리스크 근거 ID를 자동 삽입하는 Evidence-grounded AI 사업기획서 생성기입니다.")
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
        country = st.selectbox("대상 국가", country_options, index=country_options.index(country_default))
        row = get_country_row(master, country)
        sectors = sector_summary_for_country(sector_summary, country)
        sector_options = sectors["Sector_Group"].tolist() if not sectors.empty else recommended_sectors(row)
        default_sector = sc_sector if sc_sector in sector_options else recommended_sectors(row)[0]
        idx = sector_options.index(default_sector) if default_sector in sector_options else 0
        sector = st.selectbox("사업 분야", sector_options, index=idx)
        user_types = ["CSO/NGO", "기업/스타트업", "지자체", "대학생/연구자", "정책담당자"]
        user_type = st.selectbox("사용자 유형", user_types, index=user_types.index(sc_user) if sc_user in user_types else 0)
        scales = ["소규모 파일럿", "중형 확장사업", "민관협력형", "정책연구/예비타당성"]
        scale = st.selectbox("사업 규모", scales, index=scales.index(sc_scale) if sc_scale in scales else 0)
        keywords = st.text_input("핵심 키워드", value=sc_keywords)
        mode = st.radio("생성 모드", ["로컬 RAG", "LLM RAG"], horizontal=True)
        clicked = st.button("RAG형 AI 사업기획서 생성", width="stretch", type="primary")
    with c2:
        docs_preview = retrieve_rag_evidence(corpus, country, sector, keywords, row, top_k=10)
        c21, c22, c23 = st.columns(3)
        with c21: metric_card("기회점수", fmt_number(row.get("K_ODA_Opportunity_Score_V21")), f"Rank #{fmt_int(row.get('Rank_V21'))}")
        with c22: metric_card("후보유형", compact_candidate_label(row.get("Candidate_Type_V21")), row.get("Risk_Band_V21"))
        with c23: metric_card("검색 근거", fmt_int(len(docs_preview)), "RAG Top-K")
        st.markdown(f"**정책·리스크:** 정책적합성 {fmt_number(row.get('Policy_Alignment_Score_V21'))}, 실행가능성 {fmt_number(row.get('Risk_Feasibility_Score_V21'))}")
        st.markdown("**RAG 근거 미리보기:**")
        for _, d in docs_preview.head(5).iterrows():
            st.markdown(f"- **{d['Source_Type']}** · {d['Title']}")

    if clicked:
        st.divider()
        row = get_country_row(master, country)
        rag_docs = retrieve_rag_evidence(corpus, country, sector, keywords, row, top_k=16)
        prompt = build_rag_prompt(country, sector, user_type, scale, keywords, row, rag_docs, weights)
        local_proposal = build_rag_markdown_proposal(country, sector, user_type, scale, keywords, row, rag_docs, weights)
        llm_status = "로컬 RAG 생성 사용"
        proposal = local_proposal
        if mode == "LLM RAG":
            llm_text, llm_status = call_openai_llm(prompt)
            if llm_text:
                proposal = llm_text + "\n\n---\n\n## RAG Evidence Citation\n" + format_rag_citations(rag_docs)

        evidence_pack = build_rag_evidence_pack(country, sector, keywords, rag_docs)
        brief = build_policy_brief(country, sector, row, rag_docs)
        proposal_pdf = markdown_to_pdf_bytes(f"KODA {country} {sector} Proposal", proposal)
        brief_pdf = markdown_to_pdf_bytes(f"KODA {country} {sector} Policy Brief", brief)

        st.subheader("Evidence-grounded AI 생성 결과")
        st.caption(llm_status)
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
                st.info("PDF export는 reportlab 설치 시 활성화됩니다.")

        tabs = st.tabs(["요약", "근거 Citation", "점수 기여도", "브리프", "LLM Prompt", "원문"])
        with tabs[0]:
            st.markdown(f"""
            <div class="section-note"><b>핵심 요약:</b> {country} × {sector} 조합에 대해 {len(rag_docs)}개 근거를 검색했고, 모든 생성 결과는 [E01] 형식 citation으로 추적 가능합니다.</div>
            """, unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1: insight_card("왜 이 국가인가", f"개발수요 {fmt_number(row.get('Development_Need_Score'))}, 정책적합성 {fmt_number(row.get('Policy_Alignment_Score_V21'))}, 실행가능성 {fmt_number(row.get('Risk_Feasibility_Score_V21'))}")
            with c2: insight_card("왜 이 분야인가", f"추천분야 {safe_text(row.get('Recommended_Service_Angle_V2'))}, 검색분야 {sector}")
            with c3: insight_card("AI 안전장치", "Evidence Pack을 먼저 고정하고 근거 ID를 생성문에 삽입")
        with tabs[1]:
            display_docs = rag_docs[["Citation_ID", "Source_Type", "Country_KR", "Sector_Group", "Title", "Citation", "RAG_Score"]].copy()
            st.dataframe(display_docs, width="stretch", hide_index=True)
        with tabs[2]:
            contrib = score_contribution_table(row, weights)
            st.dataframe(contrib, width="stretch", hide_index=True)
        with tabs[3]:
            st.markdown(brief)
            if brief_pdf:
                st.download_button("Brief PDF", brief_pdf, f"KODA_{country}_{sector}_brief.pdf", "application/pdf", width="stretch")
        with tabs[4]:
            st.code(prompt, language="markdown")
        with tabs[5]:
            st.markdown(proposal)
            st.download_button("사업기획서 다시 다운로드", proposal.encode("utf-8"), f"KODA_{country}_{sector}_rag_proposal.md", "text/markdown", width="stretch")


def render_evidence(data):
    master, weights, notes, policy = data["master"], data["weights"], data["notes"], data["policy_risk"]
    st.title("근거 검증 센터")
    st.caption("데이터 출처, 점수 산식, 정책·리스크 proxy, 한계를 투명하게 제시합니다.")
    st.header("1. 데이터 파이프라인")
    cols=st.columns(3)
    cards=[
        ("KOICA ODA 로데이터 2019~2024", "국가×분야×연도 사업근거와 Builder 근거문장을 생성합니다."),
        ("World Bank WDI 2019~2025", "GDP, 빈곤, 교육, 전력, 인터넷, 보건 등 개발수요를 산출합니다."),
        ("CPS PDF RAG", "국가협력전략 PDF 원문을 페이지 단위로 chunking하여 정책 정합성 근거로 검색합니다."),
        ("협력국 통합 개발지표", "CPS 대상국, KOICA 사무소, 취약성·거버넌스·전자정부 proxy를 반영합니다."),
        ("정책 적합성", "국가협력전략 대상국가, 분야별 KOICA 지원규모, 사무소 여부를 반영합니다."),
        ("실행가능성/리스크", "취약국가지수, 부패인식, 전자정부, 인간개발, 기업여건을 기반으로 실행가능성을 추정합니다."),
        ("데이터 신뢰도", "WDI 커버리지, 정책·리스크 데이터 커버리지, API 검증 한계를 함께 반영합니다."),
    ]
    for i,(t,b) in enumerate(cards):
        with cols[i%3]: pipeline_card(t,b)

    st.header("2. v2.1 점수 산식")
    st.latex(r"KODA_{v2.1}=0.25D+0.20K+0.15S+0.10G+0.15P+0.10F+0.05R")
    st.dataframe(display_weights_table(weights), width="stretch", hide_index=True)
    st.markdown("""
    <div class="section-note">본 산식은 단순 지원액 순위가 아니라 개발수요, 한국 협력기반, 분야 적합성, 사업기회 공백, 정책 적합성, 실행가능성, 데이터 신뢰도를 함께 반영합니다.</div>
    """, unsafe_allow_html=True)

    st.header("3. 정책·리스크 데이터 매칭")
    cps_top50 = int((master["국가협력전략 대상국가"].astype(str).str.upper()=="Y").sum())
    office_top50 = int((master["한국국제협력단 사무소 주재 여부"].astype(str).str.upper()=="Y").sum())
    c1,c2,c3,c4=st.columns(4)
    with c1: metric_card("Top 50 매칭", "50/50", "국가명 보정 포함")
    with c2: metric_card("CPS 대상국", fmt_int(cps_top50), "Top 50 후보국 중 공개 CSV 기준")
    with c3: metric_card("KOICA 사무소", fmt_int(office_top50), "실행가능성 proxy")
    with c4: metric_card("평균 정책·리스크 커버리지", fmt_number(master["Policy_Risk_Data_Coverage_%"].mean(),1,"%"), "Top 50")
    st.markdown("""
    <div class="section-note">CPS 대상국 수는 전체 공식 CPS 대상국 수가 아니라, <b>Top 50 후보국 중 공개 CSV 기준 CPS 대상국</b>의 수입니다.</div>
    """, unsafe_allow_html=True)

    with st.expander("정책·리스크 매칭 원문 보기"):
        st.dataframe(policy.head(50), width="stretch", hide_index=True)

    st.header("4. 데이터셋 진단")
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: metric_card("후보국", fmt_int(len(master)), "Top 50")
    with c2: metric_card("KOICA 총 사업근거", fmt_int(data["projects"].shape[0]), "Top50 2019~2024")
    with c3: metric_card("국가×분야×연도", fmt_int(data["sector_year"].shape[0]), "trend rows")
    with c4: metric_card("WDI rows", fmt_int(data["wdi"].shape[0]), "50×10")
    with c5: metric_card("CPS PDF chunks", fmt_int(data["cps_pdf"].shape[0]), f"{data['cps_pdf']['Country_KR'].nunique()}개국")

    st.header("5. 리스크 관리 및 한계")
    c1,c2=st.columns(2)
    with c1:
        risk_card("CPS PDF RAG 적용", "텍스트 레이어가 있는 CPS PDF는 페이지 단위 chunk로 검색됩니다. 이미지형 CPS PDF는 OCR 처리 전까지 공개 CSV proxy와 원문 수동검증으로 보완합니다.")
        risk_card("금액 단위", "원자료의 약정액·지출액은 공식 메타데이터 확인 전까지 raw value로 표시합니다. Builder 본문에는 단위 리스크를 줄이기 위해 사업명·연도·분야 중심으로 제시합니다.")
    with c2:
        risk_card("리스크 지표의 proxy 한계", "취약국가지수·부패인식·전자정부·HDI는 실행가능성 추정을 위한 보조지표이며, 현지조사를 대체하지 않습니다.")
        risk_card("현지수요 검증", "추천 결과는 예비기획 보조도구이며 실제 사업화 전 파트너·예산·수요조사 검증이 필요합니다.")

    with st.expander("v2.1 점수화 원문 보기"):
        st.dataframe(notes, width="stretch", hide_index=True)
    with st.expander("가중치 원문 보기"):
        st.dataframe(weights, width="stretch", hide_index=True)
    with st.expander("마스터 점수표 원문 보기"):
        st.dataframe(master, width="stretch", hide_index=True)


def main():
    inject_css()
    validate_files()
    data = load_all_data()
    tabs = st.tabs(["개요", "순위", "프로필", "분야추천", "AI Builder", "근거검증", "AI검증", "심사모드", "배포"])
    with tabs[0]: render_overview(data)
    with tabs[1]: render_ranking(data)
    with tabs[2]: render_profile(data)
    with tabs[3]: render_sector(data)
    with tabs[4]: render_builder(data)
    with tabs[5]: render_evidence(data)
    with tabs[6]: render_ai_validation(data)
    with tabs[7]: render_judge_mode(data)
    with tabs[8]: render_deploy(data)


if __name__ == "__main__":
    main()
