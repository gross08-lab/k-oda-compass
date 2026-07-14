from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "artifacts" / "ai_upgrade" / "baseline_outputs"
AUDIT_FILES = (
    OUTPUT_DIR / "baseline_proposal.md",
    OUTPUT_DIR / "baseline_brief.md",
    OUTPUT_DIR / "baseline_evidence_pack.md",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def parse_evidence_pack(path: Path) -> dict[str, dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    sections = re.split(r"(?m)^## \[(E\d{2})\] ", text)
    evidence: dict[str, dict[str, str]] = {}
    for index in range(1, len(sections), 2):
        evidence_id = sections[index]
        block = sections[index + 1]
        fields = {
            match.group(1).strip(): match.group(2).strip()
            for match in re.finditer(r"(?m)^- ([^:\n]+): (.*)$", block)
        }
        title = block.splitlines()[0].strip()
        dataset = fields.get("데이터셋·문서명", "")
        source_file = fields.get("원자료 파일명", "")
        if dataset.endswith(".pdf") or source_file == "KODA_cps_pdf_chunks.csv":
            source_type = "CPS PDF"
        elif dataset == "KOICA 사업정보":
            source_type = "KOICA Project"
        elif "WDI" in dataset or "WDI" in title:
            source_type = "WDI"
        elif "sector" in source_file.lower() or "portfolio" in title.lower():
            source_type = "Sector Portfolio"
        elif "policy" in source_file.lower() or "risk" in title.lower():
            source_type = "Policy/Risk"
        elif "master_score" in source_file:
            source_type = "Score Model"
        else:
            source_type = "Other"
        relevance = fields.get("직접·보조 구분", "")
        evidence[evidence_id] = {
            "evidence_id": evidence_id,
            "title": title,
            "source_type": source_type,
            "country": fields.get("국가", ""),
            "sector": fields.get("분야", ""),
            "source_file": source_file,
            "pdf_file": dataset if dataset.endswith(".pdf") else "",
            "page": fields.get("페이지", ""),
            "chunk_id": fields.get("청크 ID", ""),
            "excerpt": fields.get("근거 요약", ""),
            "relevance": relevance,
            "proposal_excluded": "제외" in relevance or "불일치" in relevance,
        }
    return evidence


def source_checks(evidence: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    chunks = {row["Chunk_ID"]: row for row in read_csv(ROOT / "KODA_cps_pdf_chunks.csv")}
    pages = {
        (row["PDF_File"], int(float(row["Page"]))): row
        for row in read_csv(ROOT / "data" / "cps_page_text.csv")
    }
    manifest = {row["PDF_File"]: row for row in read_csv(ROOT / "data" / "cps_document_manifest.csv")}
    rows = []
    for evidence_id, item in evidence.items():
        if item["source_type"] != "CPS PDF":
            continue
        chunk = chunks.get(item["chunk_id"])
        pdf_path = ROOT / "data" / "cps_pdfs" / item["pdf_file"]
        page_number = int(item["page"]) if item["page"].isdigit() else -1
        page = pages.get((item["pdf_file"], page_number))
        excerpt = normalize(item["excerpt"].rstrip("…"))
        page_text = normalize(page.get("Text", "") if page else "")
        checks = {
            "chunk_exists": chunk is not None,
            "document_exists": pdf_path.exists(),
            "page_in_range": 1 <= page_number <= int(manifest.get(item["pdf_file"], {}).get("Pages", 0)),
            "page_cache_exists": page is not None,
            "country_match": bool(chunk) and chunk.get("Country_KR") == item["country"],
            "page_match": bool(chunk) and int(float(chunk.get("Page", -1))) == page_number,
            "excerpt_in_page_cache": bool(excerpt) and excerpt in page_text,
            "document_hash_match": pdf_path.exists()
            and sha256_file(pdf_path) == manifest.get(item["pdf_file"], {}).get("SHA256"),
            "chunk_hash_match": bool(chunk)
            and chunk.get("Source_SHA256") == manifest.get(item["pdf_file"], {}).get("SHA256"),
        }
        rows.append(
            {
                "evidence_id": evidence_id,
                "chunk_id": item["chunk_id"],
                "pdf_file": item["pdf_file"],
                "page": page_number,
                **checks,
                "status": "PASS" if all(checks.values()) else "FAIL",
            }
        )
    return rows


def occurrence_checks(evidence: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for path in AUDIT_FILES:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for match in re.finditer(r"\[(E\d{2})\]", line):
                evidence_id = match.group(1)
                item = evidence.get(evidence_id)
                is_inventory = path.name == "baseline_evidence_pack.md"
                excluded_violation = bool(
                    item and item["proposal_excluded"] and not is_inventory
                )
                rows.append(
                    {
                        "output_file": str(path.relative_to(ROOT)),
                        "line": line_number,
                        "evidence_id": evidence_id,
                        "evidence_exists": item is not None,
                        "evidence_pack_included": item is not None,
                        "excluded_id_misused": excluded_violation,
                        "status": "PASS" if item is not None and not excluded_violation else "FAIL",
                    }
                )
    return rows


def semantic_rule_checks(
    evidence: dict[str, dict[str, str]], proposal_path: Path
) -> list[dict[str, Any]]:
    rules = (
        ("CPS policy claim", ("CPS", "국가협력전략", "정책원문"), {"CPS PDF"}),
        ("KOICA experience claim", ("기존 KOICA 사업", "협력경험"), {"KOICA Project", "Sector Portfolio"}),
        ("execution-risk claim", ("실행환경", "실행가능성", "집행위험", "리스크"), {"Policy/Risk"}),
        ("country-development-context claim", ("국가 개발여건",), {"WDI"}),
    )
    rows = []
    for line_number, line in enumerate(
        proposal_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        fragments = [
            fragment.strip()
            for fragment in re.split(r"(?<=[.!?])\s+", line)
            if fragment.strip()
        ]
        for fragment in fragments:
            cited_ids = re.findall(r"\[(E\d{2})\]", fragment)
            if not cited_ids:
                continue
            for claim_type, keywords, allowed in rules:
                if not any(keyword.lower() in fragment.lower() for keyword in keywords):
                    continue
                if (
                    claim_type == "execution-risk claim"
                    and "후보유형" in fragment
                    and not any(term in fragment for term in ("실행환경", "실행가능성", "집행위험"))
                ):
                    continue
                invalid = [
                    evidence_id
                    for evidence_id in cited_ids
                    if evidence.get(evidence_id, {}).get("source_type") not in allowed
                ]
                rows.append(
                    {
                        "line": line_number,
                        "claim_type": claim_type,
                        "citation_ids": "|".join(cited_ids),
                        "allowed_source_types": "|".join(sorted(allowed)),
                        "invalid_ids": "|".join(invalid),
                        "status": "PASS" if not invalid else "REVIEW",
                        "text": fragment[:300],
                    }
                )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(rows[0]) if rows else ["status"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    evidence = parse_evidence_pack(OUTPUT_DIR / "baseline_evidence_pack.md")
    occurrences = occurrence_checks(evidence)
    sources = source_checks(evidence)
    semantics = semantic_rule_checks(evidence, OUTPUT_DIR / "baseline_proposal.md")
    spotcheck_paths = (
        ROOT / "artifacts" / "ai_upgrade" / "baseline_citation_spotcheck.csv",
        ROOT / "artifacts" / "ai_upgrade" / "baseline_rwanda_citation_recheck.csv",
    )
    spotchecks = [row for path in spotcheck_paths for row in read_csv(path)]
    exact_spotchecks = sum(row.get("source_text_match") == "EXACT_NORMALIZED_MATCH" for row in spotchecks)
    occurrence_pass = sum(row["status"] == "PASS" for row in occurrences)
    source_pass = sum(row["status"] == "PASS" for row in sources)
    semantic_review = sum(row["status"] != "PASS" for row in semantics)
    summary = {
        "audit_date": date.today().isoformat(),
        "scope": [str(path.relative_to(ROOT)) for path in AUDIT_FILES],
        "evidence_objects": len(evidence),
        "citation_occurrences": len(occurrences),
        "citation_occurrences_resolved": occurrence_pass,
        "structural_resolution_rate": occurrence_pass / len(occurrences) if occurrences else None,
        "excluded_id_violations": sum(row["excluded_id_misused"] for row in occurrences),
        "cps_evidence_objects": len(sources),
        "cps_source_chain_pass": source_pass,
        "original_pdf_spotchecks": len(spotchecks),
        "original_pdf_exact_normalized_matches": exact_spotchecks,
        "deterministic_semantic_rule_rows": len(semantics),
        "deterministic_semantic_rule_reviews": semantic_review,
        "claim_citation_human_judgments": 0,
        "cohens_kappa": None,
        "claim_citation_status": "UNRESOLVED_NO_120_PAIR_HUMAN_JUDGMENT_TABLE",
        "status": (
            "PASS_STRUCTURAL_ONLY"
            if occurrence_pass == len(occurrences) and source_pass == len(sources)
            else "FAIL"
        ),
    }
    artifact_dir = ROOT / "artifacts" / "ai_upgrade"
    write_csv(artifact_dir / "citation_structural_occurrences.csv", occurrences)
    write_csv(artifact_dir / "citation_cps_source_checks.csv", sources)
    write_csv(artifact_dir / "citation_semantic_rule_checks.csv", semantics)
    (artifact_dir / "citation_audit_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Citation Audit",
        "",
        f"- Status: **{summary['status']}**",
        f"- Structured result evidence objects: {summary['evidence_objects']}",
        f"- Citation occurrences resolved: {occurrence_pass}/{len(occurrences)}",
        f"- Excluded-ID misuse: {summary['excluded_id_violations']}",
        f"- CPS source-chain checks: {source_pass}/{len(sources)}",
        f"- Original-PDF normalized text spot-checks: {exact_spotchecks}/{len(spotchecks)}",
        f"- Deterministic claim/source-type rule reviews: {semantic_review}/{len(semantics)}",
        "- Human Claim-Citation judgments: 0; the proposed 120-pair table and Cohen's kappa are unresolved.",
        "- Scope is the current baseline Proposal, Brief, and Evidence Pack. This is not an external accuracy certification.",
    ]
    (artifact_dir / "citation_audit_report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))
    if summary["status"] == "FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
