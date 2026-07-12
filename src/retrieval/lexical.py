from __future__ import annotations

import re
from typing import Any, Iterable

from .base import RetrievalQuery


STOPWORDS = {
    "and", "or", "the", "for", "with", "from", "this", "that", "into", "based",
    "사업", "기반", "추천", "분야", "국가", "데이터", "개발", "협력", "지원",
    "검토", "활용", "기획", "파일럿", "프로젝트", "서비스", "정책", "리스크",
}


def tokenize(*parts: Any) -> set[str]:
    text = " ".join("" if part is None else str(part) for part in parts).lower()
    base_tokens = re.findall(r"[0-9a-zA-Z가-힣]+", text)
    tokens: set[str] = set()
    for token in base_tokens:
        if len(token) >= 2 and token not in STOPWORDS:
            tokens.add(token)
        if re.search(r"[가-힣]", token) and len(token) >= 4:
            for index in range(len(token) - 1):
                gram = token[index:index + 2]
                if gram not in STOPWORDS:
                    tokens.add(gram)
    return tokens


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
) -> list[tuple[int, float]]:
    query_tokens = tokenize(query.country, query.sector, query.query_text)
    scored: list[tuple[int, float]] = []
    for index, record in enumerate(records):
        if filter_metadata and not metadata_matches(record, query):
            continue
        tokens = record_tokens(record)
        score = float(len(query_tokens & tokens) * 2.0)
        if record.get("Country_KR") == query.country:
            score += 20.0
        sector = record.get("Sector_Tag", record.get("Sector_Group", ""))
        if sector == query.sector:
            score += 24.0
        haystack = f"{record.get('Text', '')} {record.get('Content', '')}"
        if query.sector and query.sector in haystack:
            score += 5.0
        if record.get("Source_Type") in {"CPS PDF", "KOICA Project"} or record.get("Chunk_ID"):
            score += 8.0
        if score > 0:
            scored.append((index, score))
    scored.sort(key=lambda item: (-item[1], item[0]))
    return scored
