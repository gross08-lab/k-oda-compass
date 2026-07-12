from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from src.retrieval import RetrievalEngine, RetrievalQuery
from src.retrieval.base import REQUIRED_RESULT_FIELDS
from src.retrieval.embedding import EmbeddingProviderUnavailable
from src.retrieval.index import load_index, save_index, sha256_file, stale_index_reason
from src.retrieval.metrics import ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank


def write_fixture(root: Path) -> None:
    rows = [
        {
            "Country_KR": "국가A",
            "Sector_Tag": "교육",
            "PDF_File": "A.pdf",
            "Page": "3",
            "Chunk_ID": "A-1",
            "Text": "직업기술교육과 디지털 교육 역량 강화",
        },
        {
            "Country_KR": "국가B",
            "Sector_Tag": "보건의료",
            "PDF_File": "B.pdf",
            "Page": "5",
            "Chunk_ID": "B-1",
            "Text": "지역 보건 전달체계 강화",
        },
    ]
    with (root / "chunks.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    config = {
        "source": {"chunk_file": "chunks.csv"},
        "embedding": {"model_name": "missing", "cache_dir": ".cache", "threads": 1},
        "index": {"file": "index.npz", "metadata": "index.json"},
        "hybrid": {"lexical_weight": 0.5, "embedding_weight": 0.5},
    }
    (root / "config.json").write_text(json.dumps(config), encoding="utf-8")


def test_lexical_schema_and_metadata_filter(tmp_path: Path) -> None:
    write_fixture(tmp_path)
    engine = RetrievalEngine(tmp_path, tmp_path / "config.json")
    query = RetrievalQuery("q1", "디지털 교육", "국가A", "교육")
    rows, status = engine.search(query, "lexical", 5)
    assert status["effective_mode"] == "lexical"
    assert [row["chunk_id"] for row in rows] == ["A-1"]
    assert tuple(rows[0]) == REQUIRED_RESULT_FIELDS


def test_embedding_failure_falls_back_without_crash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_fixture(tmp_path)
    engine = RetrievalEngine(tmp_path, tmp_path / "config.json")
    monkeypatch.setattr(engine, "_load_embedding", lambda: (_ for _ in ()).throw(EmbeddingProviderUnavailable("offline")))
    rows, status = engine.search(RetrievalQuery("q", "교육", "국가A", "교육"), "embedding", 5)
    assert rows and status["fallback"] is True
    assert status["effective_mode"] == "lexical"


def test_embedding_failure_can_be_strict(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_fixture(tmp_path)
    engine = RetrievalEngine(tmp_path, tmp_path / "config.json")
    monkeypatch.setattr(engine, "_load_embedding", lambda: (_ for _ in ()).throw(EmbeddingProviderUnavailable("offline")))
    with pytest.raises(RuntimeError):
        engine.search(RetrievalQuery("q", "교육", "국가A", "교육"), "embedding", 5, allow_fallback=False)


def test_index_round_trip_and_staleness(tmp_path: Path) -> None:
    source = tmp_path / "chunks.csv"
    source.write_text("a,b\n1,2\n", encoding="utf-8")
    records = [{"Chunk_ID": "x"}, {"Chunk_ID": "y"}]
    vectors = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    metadata = {"source_sha256": sha256_file(source)}
    save_index(vectors, records, tmp_path / "index.npz", tmp_path / "meta.json", metadata)
    ids, loaded = load_index(tmp_path / "index.npz")
    assert ids == ["x", "y"]
    assert np.allclose(loaded, vectors)
    assert stale_index_reason(tmp_path / "meta.json", source) is None
    source.write_text("changed", encoding="utf-8")
    assert stale_index_reason(tmp_path / "meta.json", source).startswith("stale embedding index")


def test_ranking_metrics() -> None:
    ranked = ["x", "target", "z"]
    expected = {"target"}
    assert recall_at_k(ranked, expected, 1) == 0.0
    assert recall_at_k(ranked, expected, 3) == 1.0
    assert precision_at_k(ranked, expected, 5) == 0.2
    assert reciprocal_rank(ranked, expected) == 0.5
    assert 0.0 < ndcg_at_k(ranked, expected, 5) < 1.0


def test_gold_split_is_deterministic() -> None:
    query_id = "GOLD-RWA_TECH-DIRECT_KEYWORD"
    first = hashlib.sha256(f"koda-retrieval-v1|{query_id}".encode()).hexdigest()
    second = hashlib.sha256(f"koda-retrieval-v1|{query_id}".encode()).hexdigest()
    assert first == second
