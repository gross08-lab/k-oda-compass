from __future__ import annotations

from dataclasses import dataclass
from typing import Any


REQUIRED_RESULT_FIELDS = (
    "query_id",
    "retrieval_mode",
    "rank",
    "country",
    "sector",
    "chunk_id",
    "document_name",
    "pdf_page",
    "lexical_score",
    "embedding_score",
    "hybrid_score",
    "evidence_class",
    "source_text",
    "retrieval_latency_ms",
)


@dataclass(frozen=True)
class RetrievalQuery:
    query_id: str
    query_text: str
    country: str
    sector: str
    evidence_class: str = "Source Evidence"


def result_row(
    query: RetrievalQuery,
    mode: str,
    rank: int,
    record: dict[str, Any],
    *,
    lexical_score: float | None,
    embedding_score: float | None,
    hybrid_score: float | None,
    latency_ms: float,
) -> dict[str, Any]:
    row = {
        "query_id": query.query_id,
        "retrieval_mode": mode,
        "rank": rank,
        "country": record.get("Country_KR", ""),
        "sector": record.get("Sector_Tag", record.get("Sector_Group", "")),
        "chunk_id": record.get("Chunk_ID", record.get("Doc_ID", "")),
        "document_name": record.get("PDF_File", record.get("Dataset_Name", "")),
        "pdf_page": record.get("Page", ""),
        "lexical_score": lexical_score,
        "embedding_score": embedding_score,
        "hybrid_score": hybrid_score,
        "evidence_class": record.get("Evidence_Class", "Source Evidence"),
        "source_text": record.get("Text", record.get("Content", "")),
        "retrieval_latency_ms": round(latency_ms, 3),
    }
    return {field: row[field] for field in REQUIRED_RESULT_FIELDS}
