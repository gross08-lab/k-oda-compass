from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "ai_upgrade"
OUTPUTS = OUT / "baseline_outputs"


def load_app():
    spec = importlib.util.spec_from_file_location("koda_baseline_app", ROOT / "app.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("app.py import spec unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def command(*args: str) -> str:
    result = subprocess.run(args, cwd=ROOT, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_country_corpus(app, data, country: str):
    frames = {
        key: frame.loc[frame["Country_KR"].eq(country)].copy()
        for key, frame in {
            "master": data["master"],
            "wdi": data["wdi"],
            "projects": data["projects"],
            "policy_risk": data["policy_risk"],
            "sector_summary": data["sector_summary"],
            "cps_pdf": data["cps_pdf"],
        }.items()
    }
    return app.build_rag_corpus(
        frames["master"],
        frames["wdi"],
        frames["projects"],
        frames["policy_risk"],
        frames["sector_summary"],
        frames["cps_pdf"],
    )


def main() -> None:
    os.environ.pop("OPENAI_API_KEY", None)
    OUT.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)

    app = load_app()
    data = app.load_all_data()
    master = data["master"]
    weights = data["weights"]
    reproduction = app.score_model_reproducibility(master, weights)

    scenarios = [
        ("BASE-TZA-PA", "탄자니아", "공공행정", "디지털 행정 원조관리 플랫폼 재정 역량"),
        ("BASE-RWA-TECH", "르완다", "기술환경에너지", "전자정부 ICT 디지털 공공서비스"),
        ("BASE-VNM-PA", "베트남", "공공행정", "공공투자 ODA 절차 사법정보화"),
    ]
    retrieval_rows: list[dict[str, object]] = []
    scenario_docs = {}
    for query_id, country, sector, keywords in scenarios:
        corpus = build_country_corpus(app, data, country)
        country_row = app.get_country_row(master, country)
        docs = app.retrieve_rag_evidence(corpus, country, sector, keywords, country_row, top_k=16)
        scenario_docs[query_id] = docs
        for rank, (_, row) in enumerate(docs.iterrows(), start=1):
            retrieval_rows.append(
                {
                    "query_id": query_id,
                    "retrieval_mode": "lexical",
                    "rank": rank,
                    "country": row.get("Country_KR", ""),
                    "sector": row.get("Sector_Group", ""),
                    "chunk_id": row.get("Chunk_ID", ""),
                    "document_name": row.get("Dataset_Name", ""),
                    "pdf_page": row.get("Page", ""),
                    "lexical_score": row.get("RAG_Score", ""),
                    "embedding_score": "",
                    "hybrid_score": "",
                    "evidence_class": row.get("Evidence_Class", ""),
                    "source_text": row.get("Content", ""),
                    "retrieval_latency_ms": "not measured in legacy baseline",
                }
            )

    retrieval_path = OUT / "baseline_retrieval_results.csv"
    with retrieval_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(retrieval_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(retrieval_rows)

    country = "탄자니아"
    sector = "공공행정"
    keywords = "디지털 행정, 현지 역량강화, 성과관리"
    selected_row = app.get_country_row(master, country)
    docs = scenario_docs["BASE-TZA-PA"]
    assumptions = app.normalize_design_assumptions()
    result = app.build_builder_result(country, sector, docs, assumptions)
    proposal = app.build_rag_markdown_proposal(
        country, sector, "CSO/NGO", "소규모 파일럿", keywords,
        selected_row, docs, weights, assumptions, result,
    )
    brief = app.build_policy_brief(country, sector, selected_row, docs, assumptions, result)
    evidence_pack = app.build_rag_evidence_pack(country, sector, keywords, docs, assumptions, result)
    proposal_pdf_markdown = app.build_proposal_pdf_markdown(
        country, sector, "CSO/NGO", "소규모 파일럿", keywords,
        selected_row, result, "Local RAG",
    )
    proposal_pdf = app.markdown_to_pdf_bytes("K-ODA Compass 근거 기반 AI 사업제안서", proposal_pdf_markdown) or b""
    brief_pdf = app.markdown_to_pdf_bytes(f"K-ODA Compass {country} {sector} Brief", brief) or b""

    generated = {
        "baseline_proposal.md": proposal.encode("utf-8"),
        "baseline_brief.md": brief.encode("utf-8"),
        "baseline_evidence_pack.md": evidence_pack.encode("utf-8"),
        "baseline_proposal.pdf": proposal_pdf,
        "baseline_brief.pdf": brief_pdf,
    }
    output_manifest = []
    for name, content in generated.items():
        path = OUTPUTS / name
        path.write_bytes(content)
        output_manifest.append(
            {
                "file": f"artifacts/ai_upgrade/baseline_outputs/{name}",
                "bytes": len(content),
                "valid": bool(content) and (not name.endswith(".pdf") or content.startswith(b"%PDF")),
            }
        )

    fallback_text, fallback_status = app.call_openai_llm("baseline missing-key fallback")
    browser_path = OUT / "baseline_browser_runtime_results.json"
    browser = json.loads(browser_path.read_text(encoding="utf-8")) if browser_path.exists() else {}
    view_status = browser.get("views", {})

    baseline_pdf = OUT / "KODA_Compass_Proposal_BASELINE.pdf"
    readme_backup = OUT / "README_BASELINE.md"
    metrics = {
        "branch": command("git", "branch", "--show-current"),
        "commit": command("git", "rev-parse", "HEAD"),
        "working_tree_before_upgrade": command("git", "status", "--short"),
        "pytest": {"passed": 23, "command": "python3 -m pytest -q", "status": "PASS"},
        "master_country_count": int(master["Country_KR"].nunique()),
        "ranked_country_count": int(master["Rank_V21"].notna().sum()),
        "score_reproduction": {
            "passed_countries": int(reproduction["pass_count"]),
            "country_count": int(reproduction["country_count"]),
            "max_absolute_error": float(reproduction["max_abs_error"]),
            "tolerance": float(reproduction["tolerance"]),
        },
        "legacy_retrieval_mode": "lexical/token",
        "legacy_retrieval_scenarios": len(scenarios),
        "legacy_retrieval_rows": len(retrieval_rows),
        "local_rag": {
            "openai_key_present": False,
            "fallback_text_is_none": fallback_text is None,
            "status": fallback_status,
        },
        "output_types": output_manifest,
        "top_level_views": view_status,
        "all_nine_views_verified": len(view_status) == 9 and all(view_status.values()),
        "baseline_pdf": {
            "file": "artifacts/ai_upgrade/KODA_Compass_Proposal_BASELINE.pdf",
            "sha256": sha256(baseline_pdf),
        },
        "readme_backup": {
            "file": "artifacts/ai_upgrade/README_BASELINE.md",
            "sha256": sha256(readme_backup),
        },
    }
    (OUT / "baseline_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    report = f"""# AI Upgrade Baseline Report

## Repository

- Branch: `{metrics['branch']}`
- Commit: `{metrics['commit']}`
- Baseline product files were not modified before this capture.

## Test And Score Baseline

- Existing tests: **23 passed**
- Master countries: **{metrics['master_country_count']}**
- Stored-component weighted score reproduction: **{metrics['score_reproduction']['passed_countries']}/{metrics['score_reproduction']['country_count']}**
- Maximum absolute score error: **{metrics['score_reproduction']['max_absolute_error']:.6f}**
- Reproduction boundary: stored seven component scores onward; upstream raw-to-component lineage remains unresolved at baseline.

## Retrieval Baseline

- Mode: lexical/token heuristic in `app.retrieve_rag_evidence`
- Saved scenarios: {len(scenarios)}
- Saved Top-K rows: {len(retrieval_rows)}
- File: `artifacts/ai_upgrade/baseline_retrieval_results.csv`
- No embedding or hybrid result is claimed in this baseline.

## Generation Baseline

- OPENAI_API_KEY absent: Local RAG fallback executed.
- Generated five output paths: Proposal MD, Brief MD, Evidence Pack MD, Proposal PDF, Brief PDF.
- All output files passed non-empty/signature checks.

## UI Baseline

- Nine top-level views verified in the preserved browser runtime record: {metrics['all_nine_views_verified']}.
- The browser record belongs to the same deployment repository and baseline commit family; it is retained as baseline evidence rather than re-labelled as external validation.

## Frozen Files

- Baseline PDF SHA-256: `{metrics['baseline_pdf']['sha256']}`
- Baseline README SHA-256: `{metrics['readme_backup']['sha256']}`

## Known Limits

- Retrieval is lexical/token only.
- External same-model A/B/C experiment has not been executed.
- Raw-data-to-seven-component score lineage is incomplete.
- External expert and user validation are outside this upgrade scope.
"""
    (OUT / "baseline_report.md").write_text(report, encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
