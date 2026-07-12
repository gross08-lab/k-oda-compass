from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/retrieval.yaml")
    args = parser.parse_args()

    import sys
    sys.path.insert(0, str(ROOT))
    from src.retrieval.embedding import FastEmbedProvider
    from src.retrieval.hybrid import load_config
    from src.retrieval.index import document_text, load_cps_records, save_index, sha256_file

    config_path = ROOT / args.config
    config = load_config(config_path)
    chunk_path = ROOT / config["source"]["chunk_file"]
    records = load_cps_records(chunk_path)
    embedding_config = config["embedding"]
    provider = FastEmbedProvider(
        model_name=embedding_config["model_name"],
        cache_dir=ROOT / embedding_config["cache_dir"],
        threads=int(embedding_config.get("threads", 2)),
    )

    documents = [document_text(record) for record in records]
    started = time.perf_counter()
    vectors = provider.encode(documents)
    build_seconds = time.perf_counter() - started
    if vectors.shape != (len(records), int(embedding_config["dimension"])):
        raise RuntimeError(f"unexpected embedding shape: {vectors.shape}")

    cache_dir = ROOT / embedding_config["cache_dir"]
    model_files = []
    for path in sorted(cache_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".onnx", ".json", ".txt", ".model"}:
            model_files.append(
                {
                    "relative_file": str(path.relative_to(cache_dir)),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )

    index_path = ROOT / config["index"]["file"]
    metadata_path = ROOT / config["index"]["metadata"]
    metadata = {
        "schema_version": 1,
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_file": config["source"]["chunk_file"],
        "source_sha256": sha256_file(chunk_path),
        "source_rows": len(records),
        "valid_rows": sum(bool(record.get("Chunk_ID") and record.get("Text")) for record in records),
        "model_name": embedding_config["model_name"],
        "fastembed_version": embedding_config["runtime_version"],
        "dimension": int(vectors.shape[1]),
        "license": embedding_config["license"],
        "pooling_note": "FastEmbed 0.8.0 mean-pooling implementation; fixed for this benchmark snapshot",
        "build_seconds": round(build_seconds, 6),
        "vector_bytes_uncompressed": int(vectors.nbytes),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "model_files": model_files,
    }
    save_index(vectors, records, index_path, metadata_path, metadata)
    metadata["index_file"] = str(index_path.relative_to(ROOT))
    metadata["index_bytes"] = index_path.stat().st_size
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
