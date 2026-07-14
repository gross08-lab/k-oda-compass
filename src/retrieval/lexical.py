from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Iterable

from .base import RetrievalQuery


STOPWORDS = {
    "and", "or", "the", "for", "with", "from", "this", "that", "into", "based",
    "사업", "기반", "추천", "분야", "국가", "데이터", "개발", "협력", "지원",
    "검토", "활용", "기획", "파일럿", "프로젝트", "서비스", "정책", "리스크",
}

ENGLISH_ODA_TERMS = {
    "administration": ("공공행정", "행정", "거버넌스"),
    "agriculture": ("농업", "농림수산", "농촌"),
    "approval": ("승인", "시행", "절차"),
    "capacity": ("역량", "인력양성"),
    "carbon": ("탄소", "온실가스"),
    "climate": ("기후", "기후변화", "환경"),
    "digital": ("디지털", "ICT", "전자정부"),
    "distribution": ("배전", "송배전"),
    "education": ("교육", "인적자원"),
    "electricity": ("전력", "에너지", "발전"),
    "energy": ("에너지", "전력", "신재생에너지"),
    "environmental": ("환경", "친환경", "기후변화"),
    "government": ("정부", "전자정부", "공공행정"),
    "green": ("친환경", "녹색", "기후변화"),
    "health": ("보건", "의료", "보건의료"),
    "healthcare": ("보건의료", "의료서비스", "의료시설"),
    "higher": ("고등교육",),
    "hospital": ("병원", "의료시설"),
    "ict": ("ICT", "디지털", "정보통신기술"),
    "infrastructure": ("인프라", "기반시설"),
    "innovation": ("혁신", "과학기술"),
    "management": ("관리", "역량"),
    "maternal": ("모자보건",),
    "power": ("전력", "에너지", "발전"),
    "public": ("공공", "공공서비스", "공공행정"),
    "renewable": ("신재생에너지", "친환경에너지"),
    "resilience": ("회복력", "대응역량"),
    "rural": ("농촌", "지역개발"),
    "sanitation": ("위생", "상하수도"),
    "science": ("과학기술", "기술혁신"),
    "skills": ("기술인력", "역량강화"),
    "startup": ("창업", "중소기업"),
    "technology": ("기술", "ICT", "과학기술"),
    "transmission": ("송전", "송배전"),
    "transport": ("교통", "물류"),
    "vocational": ("직업훈련", "직업기술교육"),
    "water": ("물관리", "수자원", "상하수도"),
}

KOREAN_ODA_PHRASES = {
    "국가 개발여건": ("개발수요", "사회경제", "인프라"),
    "기후회복력": ("기후변화", "재해예방", "대응역량"),
    "농업 가치사슬": ("농업생산성", "농촌개발", "유통"),
    "디지털 전환": ("전자정부", "공공서비스", "ICT"),
    "보건체계": ("기초보건", "보편적 의료보장", "의료시설"),
    "양질의 의료서비스": ("의료서비스", "의료시설", "보편적 의료보장"),
    "전력 접근성": ("전력공급", "송배전", "에너지 인프라"),
    "정책방향": ("지원목표", "중점지원", "분야별 목표"),
    "중점지원 방향": ("지원목표", "중점분야", "분야별 목표"),
    "직업기술교육": ("직업훈련", "TVET", "기술인력"),
}


def expand_query_text(text: str) -> str:
    lowered = str(text).lower()
    expanded: list[str] = []
    for token in re.findall(r"[a-zA-Z]+", lowered):
        expanded.extend(ENGLISH_ODA_TERMS.get(token, ()))
    for phrase, terms in KOREAN_ODA_PHRASES.items():
        if phrase in lowered:
            expanded.extend(terms)
    return " ".join(dict.fromkeys(expanded))


def tokenize_list(*parts: Any) -> list[str]:
    text = " ".join("" if part is None else str(part) for part in parts).lower()
    base_tokens = re.findall(r"[0-9a-zA-Z가-힣]+", text)
    tokens: list[str] = []
    for token in base_tokens:
        if len(token) >= 2 and token not in STOPWORDS:
            tokens.append(token)
        if re.search(r"[가-힣]", token) and len(token) >= 4:
            for index in range(len(token) - 1):
                gram = token[index:index + 2]
                if gram not in STOPWORDS:
                    tokens.append(gram)
    return tokens


def tokenize(*parts: Any) -> set[str]:
    return set(tokenize_list(*parts))


def record_token_counts(record: dict[str, Any]) -> Counter[str]:
    cached = record.get("_LexicalTokenCounts")
    if isinstance(cached, Counter):
        return cached
    counts = Counter(
        tokenize_list(
            record.get("Country_KR"),
            record.get("Sector_Tag", record.get("Sector_Group")),
            record.get("PDF_File", record.get("Title")),
            record.get("Text", record.get("Content")),
            record.get("Citation"),
        )
    )
    record["_LexicalTokenCounts"] = counts
    return counts


def record_tokens(record: dict[str, Any]) -> set[str]:
    cached = record.get("Tokens")
    if isinstance(cached, (list, set, tuple)):
        return set(str(token) for token in cached)
    return tokenize(
        record.get("Country_KR"),
        record.get("Sector_Tag", record.get("Sector_Group")),
        record.get("PDF_File", record.get("Title")),
        record.get("Text", record.get("Content")),
        record.get("Citation"),
    )


def metadata_matches(record: dict[str, Any], query: RetrievalQuery) -> bool:
    country_match = not query.country or record.get("Country_KR") == query.country
    sector = record.get("Sector_Tag", record.get("Sector_Group", ""))
    sector_match = not query.sector or sector == query.sector
    evidence = record.get("Evidence_Class", "Source Evidence")
    evidence_match = not query.evidence_class or evidence == query.evidence_class
    return country_match and sector_match and evidence_match


def score_records(
    records: Iterable[dict[str, Any]],
    query: RetrievalQuery,
    *,
    filter_metadata: bool,
    phrase_bonus: float = 1.5,
    bm25_k1: float = 1.2,
    bm25_b: float = 0.75,
    term_coverage_weight: float = 2.0,
) -> list[tuple[int, float]]:
    record_list = list(records)
    expanded_query = expand_query_text(query.query_text)
    query_tokens = tokenize(query.country, query.sector, query.query_text, expanded_query)
    phrase_terms = [
        term.lower()
        for term in re.findall(r"[0-9a-zA-Z가-힣]+", f"{query.query_text} {expanded_query}")
        if len(term) >= 3 and term.lower() not in STOPWORDS
    ]
    candidates = [
        (index, record)
        for index, record in enumerate(record_list)
        if not filter_metadata or metadata_matches(record, query)
    ]
    token_counts = {index: record_token_counts(record) for index, record in candidates}
    document_count = len(candidates)
    average_length = (
        sum(sum(counts.values()) for counts in token_counts.values()) / document_count
        if document_count
        else 1.0
    )
    document_frequency = {
        token: sum(1 for counts in token_counts.values() if token in counts)
        for token in query_tokens
    }

    scored: list[tuple[int, float]] = []
    for index, record in candidates:
        counts = token_counts[index]
        document_length = sum(counts.values())
        score = 0.0
        for token in query_tokens:
            frequency = counts.get(token, 0)
            if not frequency:
                continue
            df = document_frequency[token]
            inverse_document_frequency = math.log(
                1.0 + (document_count - df + 0.5) / (df + 0.5)
            )
            denominator = frequency + bm25_k1 * (
                1.0 - bm25_b + bm25_b * document_length / max(average_length, 1.0)
            )
            score += inverse_document_frequency * frequency * (bm25_k1 + 1.0) / denominator
        score += len(query_tokens.intersection(counts)) * term_coverage_weight
        if record.get("Country_KR") == query.country:
            score += 20.0
        sector = record.get("Sector_Tag", record.get("Sector_Group", ""))
        if sector == query.sector:
            score += 24.0
        haystack = f"{record.get('Text', '')} {record.get('Content', '')}"
        lowered_haystack = haystack.lower()
        phrase_frequency = sum(min(lowered_haystack.count(term), 3) for term in phrase_terms)
        score += float(phrase_frequency * phrase_bonus)
        if query.sector and query.sector in haystack:
            score += 5.0
        if record.get("Source_Type") in {"CPS PDF", "KOICA Project"} or record.get("Chunk_ID"):
            score += 8.0
        if score > 0:
            scored.append((index, score))
    scored.sort(
        key=lambda item: (
            -item[1],
            str(record_list[item[0]].get("Chunk_ID", "")),
            item[0],
        )
    )
    return scored
