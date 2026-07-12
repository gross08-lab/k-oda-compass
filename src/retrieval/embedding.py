from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import numpy as np

from .index import load_index, stale_index_reason


class EmbeddingProviderUnavailable(RuntimeError):
    pass


def normalize_rows(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


class FastEmbedProvider:
    def __init__(self, model_name: str, cache_dir: Path, threads: int = 2):
        try:
            from fastembed import TextEmbedding
        except ImportError as exc:
            raise EmbeddingProviderUnavailable("fastembed is not installed") from exc
        self.model_name = model_name
        self.model = TextEmbedding(model_name=model_name, cache_dir=str(cache_dir), threads=threads)

    def encode(self, texts: Iterable[str]) -> np.ndarray:
        vectors = np.asarray(list(self.model.embed(list(texts))), dtype=np.float32)
        return normalize_rows(vectors)


class EmbeddingIndex:
    def __init__(
        self,
        index_path: Path,
        metadata_path: Path,
        chunk_path: Path,
        provider: FastEmbedProvider,
    ):
        reason = stale_index_reason(metadata_path, chunk_path)
        if reason:
            raise EmbeddingProviderUnavailable(reason)
        self.metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        self.chunk_ids, vectors = load_index(index_path)
        self.vectors = normalize_rows(vectors)
        self.provider = provider

    def score(self, query_text: str) -> np.ndarray:
        query_vector = self.provider.encode([query_text])[0]
        return self.vectors @ query_vector
