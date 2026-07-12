from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def verify_manifest(root: Path, manifest: list[dict[str, str]]) -> list[str]:
    errors = []
    for item in manifest:
        source = root / item["source_file"]
        if not source.exists():
            errors.append(f"missing:{item['source_file']}")
        elif sha256_file(source) != item["sha256"]:
            errors.append(f"hash:{item['source_file']}")
    return errors


def load_score_sources(root: Path, config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    master = pd.read_csv(root / config["master_file"], encoding="utf-8-sig")
    weights = pd.read_csv(root / config["weights_file"], encoding="utf-8-sig")
    return master, weights
