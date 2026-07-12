from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_cps_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["Evidence_Class"] = "Source Evidence"
        try:
            row["Page"] = int(float(row.get("Page") or 0))
        except ValueError:
            row["Page"] = 0
    return rows


def document_text(record: dict[str, Any]) -> str:
    return " ".join(
        str(value).strip()
        for value in (
            record.get("Country_KR"),
            record.get("Sector_Tag"),
            record.get("PDF_File"),
            record.get("Text"),
        )
        if value
    )


def save_index(
    vectors: np.ndarray,
    records: list[dict[str, Any]],
    index_path: Path,
    metadata_path: Path,
    metadata: dict[str, Any],
) -> None:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    ids = np.array([record["Chunk_ID"] for record in records], dtype=str)
    np.savez_compressed(index_path, chunk_ids=ids, vectors=vectors.astype(np.float32))
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_index(index_path: Path) -> tuple[list[str], np.ndarray]:
    payload = np.load(index_path, allow_pickle=False)
    return payload["chunk_ids"].astype(str).tolist(), payload["vectors"].astype(np.float32)


def stale_index_reason(metadata_path: Path, chunk_path: Path) -> str | None:
    if not metadata_path.exists():
        return "embedding index metadata missing"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    current_hash = sha256_file(chunk_path)
    expected_hash = metadata.get("source_sha256")
    if current_hash != expected_hash:
        return f"stale embedding index: chunk hash {current_hash[:12]} != {str(expected_hash)[:12]}"
    return None
