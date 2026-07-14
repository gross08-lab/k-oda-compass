from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

from src.retrieval.hybrid import load_config


ROOT = Path(__file__).resolve().parents[1]
FINGERPRINT_COLUMNS = ("query_id", "split", "expected_chunk_ids")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def label_fingerprint(rows: list[dict[str, str]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FINGERPRINT_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows({column: row.get(column, "") for column in FINGERPRINT_COLUMNS} for row in rows)
    payload = output.getvalue()
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify(root: Path) -> dict[str, object]:
    config = load_config(root / "config" / "retrieval.yaml")["benchmark"]
    gold_path = root / "benchmarks" / "retrieval_gold_set.csv"
    with gold_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    observed = {
        "gold_file": "benchmarks/retrieval_gold_set.csv",
        "gold_sha256": sha256_file(gold_path),
        "gold_label_fingerprint": label_fingerprint(rows),
        "gold_rows": len(rows),
        "dev_rows": sum(row["split"] == "dev" for row in rows),
        "test_rows": sum(row["split"] == "test" for row in rows),
        "unique_query_ids": len({row["query_id"] for row in rows}),
    }
    expected = {key: config[key] for key in observed if key in config}
    mismatches = {
        key: {"expected": expected[key], "observed": observed[key]}
        for key in expected
        if str(expected[key]) != str(observed[key])
    }
    observed["status"] = "PASS" if not mismatches else "FAIL"
    observed["mismatches"] = mismatches
    if mismatches:
        raise RuntimeError("frozen Gold Set mismatch: " + json.dumps(mismatches, ensure_ascii=False))
    return observed


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify the frozen retrieval Gold labels and split.")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = verify(args.root.resolve())
    output = args.root / "artifacts" / "ai_upgrade" / "retrieval_gold_freeze.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
