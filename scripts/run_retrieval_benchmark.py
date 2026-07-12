from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import statistics
import time
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from src.retrieval import RetrievalEngine, RetrievalQuery
from src.retrieval.metrics import query_metrics


ROOT = Path(__file__).resolve().parents[1]
MODES = ("lexical", "embedding", "hybrid", "hybrid_filtered")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def mean(values: list[float]) -> float:
    finite = [value for value in values if not math.isnan(value)]
    return statistics.fmean(finite) if finite else float("nan")


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1)
    return ordered[index]


def run_query(
    engine: RetrievalEngine,
    query: dict[str, str],
    mode: str,
    top_k: int,
    weight: float | None,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, float]]:
    request = RetrievalQuery(
        query_id=query["query_id"],
        query_text=query["query_text"],
        country=query["country"],
        sector=query["sector"],
        evidence_class=query["evidence_class"],
    )
    weights = (weight, 1.0 - weight) if weight is not None and mode.startswith("hybrid") else None
    rows, status = engine.search(
        request,
        mode,
        top_k,
        allow_fallback=False,
        hybrid_weights=weights,
    )
    return rows, status, query_metrics(query, rows)


def aggregate(
    mode: str,
    split: str,
    records: list[dict[str, Any]],
    weight: float | None,
) -> dict[str, Any]:
    metrics = [record["metrics"] for record in records]
    positives = [metric for metric in metrics if metric["positive_query"]]
    negatives = [metric for metric in metrics if not metric["positive_query"]]
    latencies = [float(record["status"]["latency_ms"]) for record in records]
    return {
        "retrieval_mode": mode,
        "split": split,
        "queries": len(records),
        "positive_queries": len(positives),
        "negative_queries": len(negatives),
        "lexical_weight": weight if mode.startswith("hybrid") else None,
        "embedding_weight": 1.0 - weight if mode.startswith("hybrid") and weight is not None else None,
        "Recall@1": mean([metric["Recall@1"] for metric in positives]),
        "Recall@3": mean([metric["Recall@3"] for metric in positives]),
        "Recall@5": mean([metric["Recall@5"] for metric in positives]),
        "Precision@5": mean([metric["Precision@5"] for metric in positives]),
        "MRR": mean([metric["MRR"] for metric in positives]),
        "nDCG@5": mean([metric["nDCG@5"] for metric in positives]),
        "negative_rejection": mean([metric["negative_rejection"] for metric in negatives]),
        "country_mismatch": mean([metric["country_mismatch"] for metric in metrics]),
        "sector_mismatch": mean([metric["sector_mismatch"] for metric in metrics]),
        "evidence_class_mismatch": mean([metric["evidence_class_mismatch"] for metric in metrics]),
        "avg_latency_ms": mean(latencies),
        "p95_latency_ms": percentile(latencies, 0.95),
    }


def evaluate(
    engine: RetrievalEngine,
    queries: list[dict[str, str]],
    mode: str,
    top_k: int,
    weight: float | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    query_records = []
    result_rows = []
    for query in queries:
        rows, status, metrics = run_query(engine, query, mode, top_k, weight)
        query_records.append({"query": query, "status": status, "metrics": metrics})
        for row in rows:
            row.update(
                {
                    "split": query["split"],
                    "query_type": query["query_type"],
                    "query_text": query["query_text"],
                    "expected_chunk_ids": query["expected_chunk_ids"],
                    "requested_country": query["country"],
                    "requested_sector": query["sector"],
                    "fallback": status["fallback"],
                }
            )
            result_rows.append(row)
    return query_records, result_rows


def tuning_key(summary: dict[str, Any]) -> tuple[float, ...]:
    return (
        float(summary["nDCG@5"]),
        float(summary["MRR"]),
        float(summary["Recall@5"]),
        -float(summary["country_mismatch"]),
        -float(summary["sector_mismatch"]),
        -float(summary["avg_latency_ms"]),
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def render_chart(summaries: list[dict[str, Any]], path: Path) -> str | None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return "Pillow unavailable; chart not rendered"
    tests = [row for row in summaries if row["split"] == "test"]
    width, height = 1500, 800
    image = Image.new("RGB", (width, height), "#F7F8FA")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((70, 40), "K-ODA Compass retrieval benchmark - frozen test split", fill="#152238", font=font)
    metrics = ("Recall@5", "MRR", "nDCG@5")
    colors = ("#147D64", "#D77A20", "#315B9D")
    left, top, chart_w, chart_h = 100, 120, 1250, 520
    draw.line((left, top + chart_h, left + chart_w, top + chart_h), fill="#52606D", width=2)
    group_w = chart_w / max(1, len(tests))
    bar_w = 55
    for group_index, row in enumerate(tests):
        center = left + group_w * (group_index + 0.5)
        for metric_index, metric in enumerate(metrics):
            value = float(row[metric])
            x0 = center + (metric_index - 1) * (bar_w + 12) - bar_w / 2
            y0 = top + chart_h * (1.0 - value)
            draw.rectangle((x0, y0, x0 + bar_w, top + chart_h), fill=colors[metric_index])
            draw.text((x0 + 7, max(top, y0 - 18)), f"{value:.2f}", fill="#152238", font=font)
        label = row["retrieval_mode"]
        if row.get("lexical_weight") not in (None, ""):
            label += f"\nL={float(row['lexical_weight']):.1f}"
        draw.multiline_text((center - 55, top + chart_h + 20), label, fill="#152238", font=font, align="center")
    legend_x = 1030
    for index, metric in enumerate(metrics):
        draw.rectangle((legend_x, 55 + index * 24, legend_x + 15, 70 + index * 24), fill=colors[index])
        draw.text((legend_x + 22, 55 + index * 24), metric, fill="#152238", font=font)
    draw.text((70, 740), "Internal benchmark: 10 PDF pages, 60 query forms; not external validation.", fill="#52606D", font=font)
    image.save(path)
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    artifact_dir = root / "artifacts" / "ai_upgrade"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    gold = [
        row for row in read_csv(root / "benchmarks" / "retrieval_gold_set.csv")
        if row["label_verified"].lower() == "true"
    ]
    engine = RetrievalEngine(root)
    top_k = int(engine.config["benchmark"]["top_k"])
    candidates = [float(value) for value in engine.config["hybrid"]["dev_candidates"]]

    # Model initialization is excluded from per-query latency and recorded separately.
    warm_query = next(row for row in gold if row["split"] == "dev")
    warm_started = time.perf_counter()
    run_query(engine, warm_query, "embedding", top_k, None)
    warmup_ms = (time.perf_counter() - warm_started) * 1000

    dev = [row for row in gold if row["split"] == "dev"]
    test = [row for row in gold if row["split"] == "test"]
    tuning_rows = []
    for weight in candidates:
        records, _ = evaluate(engine, dev, "hybrid_filtered", top_k, weight)
        summary = aggregate("hybrid_filtered", "dev_tuning", records, weight)
        tuning_rows.append(summary)
    selected = max(tuning_rows, key=tuning_key)
    frozen_weight = float(selected["lexical_weight"])

    all_summaries = []
    all_results = []
    query_metric_rows = []
    for split, queries in (("dev", dev), ("test", test)):
        for mode in MODES:
            weight = frozen_weight if mode.startswith("hybrid") else None
            records, results = evaluate(engine, queries, mode, top_k, weight)
            all_results.extend(results)
            all_summaries.append(aggregate(mode, split, records, weight))
            for record in records:
                query_metric_rows.append(
                    {
                        "query_id": record["query"]["query_id"],
                        "split": split,
                        "retrieval_mode": mode,
                        "query_type": record["query"]["query_type"],
                        "expected_chunk_ids": record["query"]["expected_chunk_ids"],
                        **record["metrics"],
                        "latency_ms": record["status"]["latency_ms"],
                        "fallback": record["status"]["fallback"],
                    }
                )

    test_rows = [row for row in all_summaries if row["split"] == "test"]
    recommended = max(test_rows, key=tuning_key)
    index_meta = json.loads((artifact_dir / "embedding_index_metadata.json").read_text(encoding="utf-8"))
    payload = {
        "benchmark_date": date.today().isoformat(),
        "gold_queries_verified": len(gold),
        "independently_verified_pdf_pages": len({row["expected_document"] + ":" + row["expected_pdf_pages"] for row in gold}),
        "dev_queries": len(dev),
        "test_queries": len(test),
        "split_frozen_before_benchmark": True,
        "tuning_mode": "hybrid_filtered on dev only",
        "tuning_candidates": candidates,
        "frozen_lexical_weight": frozen_weight,
        "frozen_embedding_weight": 1.0 - frozen_weight,
        "embedding_model": engine.config["embedding"],
        "model_warmup_ms": round(warmup_ms, 3),
        "index_build_seconds": index_meta["build_seconds"],
        "index_bytes": index_meta["index_bytes"],
        "recommended_mode": recommended["retrieval_mode"],
        "recommendation_basis": "Frozen test nDCG@5, MRR, Recall@5, metadata mismatch and measured query latency",
        "summaries": all_summaries,
        "dev_tuning": tuning_rows,
    }
    (artifact_dir / "retrieval_benchmark_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    write_csv(artifact_dir / "retrieval_benchmark_results.csv", all_results)
    write_csv(artifact_dir / "retrieval_benchmark_query_metrics.csv", query_metric_rows)
    write_csv(artifact_dir / "retrieval_benchmark_summary.csv", all_summaries)
    write_csv(artifact_dir / "retrieval_hybrid_dev_tuning.csv", tuning_rows)
    chart_error = render_chart(all_summaries, artifact_dir / "retrieval_benchmark_comparison.png")
    if not chart_error:
        shutil.copyfile(
            artifact_dir / "retrieval_benchmark_comparison.png",
            artifact_dir / "retrieval_comparison.png",
        )
    (artifact_dir / "retrieval_errors.csv").write_text(
        "query_id,retrieval_mode,error_type,error_message\n", encoding="utf-8"
    )

    lines = [
        "# Retrieval Benchmark Report",
        "",
        "## Gold Set Boundary",
        "",
        f"- Verified query forms: {len(gold)}",
        f"- Independently checked CPS PDF pages: {payload['independently_verified_pdf_pages']}",
        f"- Frozen dev/test split: {len(dev)}/{len(test)}",
        "- Labels were frozen before any retrieval result was inspected.",
        "- This is an internal benchmark and not an external expert validation.",
        "",
        "## Controlled Retrieval Setup",
        "",
        f"- Embedding model: `{engine.config['embedding']['model_name']}`",
        f"- Runtime: FastEmbed {engine.config['embedding']['runtime_version']} / mean pooling",
        f"- Index: {index_meta['valid_rows']} CPS chunks, {index_meta['index_bytes']:,} bytes",
        f"- Build time: {index_meta['build_seconds']:.3f}s; model warm-up: {warmup_ms:.3f}ms",
        f"- Hybrid tuning: dev-only; frozen lexical/embedding weights = {frozen_weight:.1f}/{1-frozen_weight:.1f}",
        "",
        "## Frozen Test Results",
        "",
        "| Mode | Recall@1 | Recall@3 | Recall@5 | MRR | nDCG@5 | Country mismatch | Sector mismatch | Avg ms | p95 ms |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in test_rows:
        lines.append(
            f"| {row['retrieval_mode']} | {row['Recall@1']:.3f} | {row['Recall@3']:.3f} | "
            f"{row['Recall@5']:.3f} | {row['MRR']:.3f} | {row['nDCG@5']:.3f} | "
            f"{row['country_mismatch']:.3f} | {row['sector_mismatch']:.3f} | "
            f"{row['avg_latency_ms']:.2f} | {row['p95_latency_ms']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Recommended retrieval mode: `{recommended['retrieval_mode']}`.",
            "- Recommendation is limited to this frozen internal test set; it is not a universal accuracy claim.",
            "- Negative metadata queries are reported separately and are not counted as positive Recall wins.",
            "- Deployment keeps a deterministic lexical fallback when embedding dependencies or the index are unavailable.",
        ]
    )
    if chart_error:
        lines.append(f"- Visualization limitation: {chart_error}.")
    (artifact_dir / "retrieval_benchmark_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"frozen_weight": frozen_weight, "recommended": recommended}, ensure_ascii=False))


if __name__ == "__main__":
    main()
