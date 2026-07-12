from __future__ import annotations

import math
from statistics import mean
from typing import Any


def recall_at_k(ranked_ids: list[str], expected: set[str], k: int) -> float:
    if not expected:
        return 1.0 if not ranked_ids[:k] else 0.0
    return len(expected.intersection(ranked_ids[:k])) / len(expected)


def precision_at_k(ranked_ids: list[str], expected: set[str], k: int) -> float:
    if not expected:
        return 1.0 if not ranked_ids[:k] else 0.0
    return len(expected.intersection(ranked_ids[:k])) / k


def reciprocal_rank(ranked_ids: list[str], expected: set[str]) -> float:
    if not expected:
        return 1.0 if not ranked_ids else 0.0
    for rank, chunk_id in enumerate(ranked_ids, start=1):
        if chunk_id in expected:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(ranked_ids: list[str], expected: set[str], k: int) -> float:
    if not expected:
        return 1.0 if not ranked_ids[:k] else 0.0
    dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank, chunk_id in enumerate(ranked_ids[:k], start=1)
        if chunk_id in expected
    )
    ideal_hits = min(len(expected), k)
    ideal = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return dcg / ideal if ideal else 0.0


def query_metrics(query: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, float]:
    expected = set(filter(None, str(query.get("expected_chunk_ids", "")).split("|")))
    ranked_ids = [str(row["chunk_id"]) for row in rows]
    positive = bool(expected)
    return {
        "positive_query": float(positive),
        "Recall@1": recall_at_k(ranked_ids, expected, 1),
        "Recall@3": recall_at_k(ranked_ids, expected, 3),
        "Recall@5": recall_at_k(ranked_ids, expected, 5),
        "Precision@5": precision_at_k(ranked_ids, expected, 5),
        "MRR": reciprocal_rank(ranked_ids, expected),
        "nDCG@5": ndcg_at_k(ranked_ids, expected, 5),
        "negative_rejection": float(not ranked_ids) if not positive else float("nan"),
        "country_mismatch": mean(
            [float(row["country"] != query.get("country")) for row in rows]
        ) if rows else 0.0,
        "sector_mismatch": mean(
            [float(row["sector"] != query.get("sector")) for row in rows]
        ) if rows else 0.0,
        "evidence_class_mismatch": mean(
            [float(row["evidence_class"] != query.get("evidence_class")) for row in rows]
        ) if rows else 0.0,
    }
