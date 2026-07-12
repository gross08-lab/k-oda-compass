from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from .base import RetrievalQuery, result_row
from .embedding import EmbeddingIndex, EmbeddingProviderUnavailable, FastEmbedProvider
from .index import load_cps_records
from .lexical import metadata_matches, score_records


class RetrievalUnavailable(RuntimeError):
    pass


def minmax(values: np.ndarray) -> np.ndarray:
    if values.size == 0:
        return values
    minimum = float(values.min())
    maximum = float(values.max())
    if maximum == minimum:
        return np.ones_like(values) if maximum > 0 else np.zeros_like(values)
    return (values - minimum) / (maximum - minimum)


def load_config(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError:
        yaml = None
    if yaml is not None:
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    # The committed file is JSON-compatible YAML, so stdlib parsing is a safe fallback.
    return json.loads(path.read_text(encoding="utf-8"))


class RetrievalEngine:
    def __init__(self, root: Path, config_path: Path | None = None):
        self.root = root
        self.config_path = config_path or root / "config" / "retrieval.yaml"
        self.config = load_config(self.config_path)
        chunk_path = root / self.config["source"]["chunk_file"]
        self.chunk_path = chunk_path
        self.records = load_cps_records(chunk_path)
        self.by_id = {record["Chunk_ID"]: record for record in self.records}
        self._embedding_index: EmbeddingIndex | None = None

    def _load_embedding(self) -> EmbeddingIndex:
        if self._embedding_index is not None:
            return self._embedding_index
        embedding = self.config["embedding"]
        provider = FastEmbedProvider(
            model_name=embedding["model_name"],
            cache_dir=self.root / embedding["cache_dir"],
            threads=int(embedding.get("threads", 2)),
        )
        index = self.config["index"]
        self._embedding_index = EmbeddingIndex(
            index_path=self.root / index["file"],
            metadata_path=self.root / index["metadata"],
            chunk_path=self.chunk_path,
            provider=provider,
        )
        return self._embedding_index

    def search(
        self,
        query: RetrievalQuery,
        mode: str,
        top_k: int = 5,
        *,
        allow_fallback: bool = True,
        hybrid_weights: tuple[float, float] | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        if mode not in {"lexical", "embedding", "hybrid", "hybrid_filtered"}:
            raise ValueError(f"unknown retrieval mode: {mode}")
        started = time.perf_counter()
        requested_mode = mode
        fallback_reason = None

        lexical_filtered = mode == "lexical"
        lexical_pairs = score_records(self.records, query, filter_metadata=lexical_filtered)
        lexical_raw = np.zeros(len(self.records), dtype=np.float32)
        for index, score in lexical_pairs:
            lexical_raw[index] = score

        embedding_raw = np.zeros(len(self.records), dtype=np.float32)
        if mode != "lexical":
            try:
                embedding_index = self._load_embedding()
                index_scores = embedding_index.score(query.query_text)
                id_to_score = dict(zip(embedding_index.chunk_ids, index_scores.tolist()))
                embedding_raw = np.array(
                    [float(id_to_score.get(record["Chunk_ID"], 0.0)) for record in self.records],
                    dtype=np.float32,
                )
            except (EmbeddingProviderUnavailable, FileNotFoundError, ValueError) as exc:
                if not allow_fallback:
                    raise RetrievalUnavailable(str(exc)) from exc
                fallback_reason = str(exc)
                mode = "lexical"
                lexical_pairs = score_records(self.records, query, filter_metadata=True)
                lexical_raw[:] = 0
                for index, score in lexical_pairs:
                    lexical_raw[index] = score

        if mode == "lexical":
            candidate_indices = [index for index, score in lexical_pairs if score > 0]
            final_scores = lexical_raw
        else:
            if mode == "hybrid_filtered":
                candidate_indices = [
                    index for index, record in enumerate(self.records) if metadata_matches(record, query)
                ]
            else:
                candidate_indices = list(range(len(self.records)))

            if mode == "embedding":
                final_scores = embedding_raw
            else:
                lexical_weight, embedding_weight = hybrid_weights or (
                    float(self.config["hybrid"]["lexical_weight"]),
                    float(self.config["hybrid"]["embedding_weight"]),
                )
                lex_norm = np.zeros(len(self.records), dtype=np.float32)
                emb_norm = np.zeros(len(self.records), dtype=np.float32)
                if candidate_indices:
                    lex_values = minmax(lexical_raw[candidate_indices])
                    emb_values = minmax(embedding_raw[candidate_indices])
                    lex_norm[candidate_indices] = lex_values
                    emb_norm[candidate_indices] = emb_values
                final_scores = lexical_weight * lex_norm + embedding_weight * emb_norm

            candidate_indices.sort(key=lambda index: (-float(final_scores[index]), index))

        selected = [index for index in candidate_indices if float(final_scores[index]) > 0][:top_k]
        elapsed_ms = (time.perf_counter() - started) * 1000
        rows = []
        for rank, index in enumerate(selected, start=1):
            rows.append(
                result_row(
                    query,
                    mode,
                    rank,
                    self.records[index],
                    lexical_score=float(lexical_raw[index]),
                    embedding_score=float(embedding_raw[index]) if requested_mode != "lexical" and fallback_reason is None else None,
                    hybrid_score=float(final_scores[index]) if mode.startswith("hybrid") else None,
                    latency_ms=elapsed_ms,
                )
            )
        status = {
            "requested_mode": requested_mode,
            "effective_mode": mode,
            "fallback": fallback_reason is not None,
            "fallback_reason": fallback_reason,
            "result_count": len(rows),
            "latency_ms": round(elapsed_ms, 3),
        }
        return rows, status
