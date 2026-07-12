from __future__ import annotations

import argparse
import csv
import hashlib
import re
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]


CASES = [
    {
        "case": "RWA_TECH",
        "chunk_id": "CPS-RWA-p26-01",
        "country": "르완다",
        "sector": "기술환경에너지",
        "direct": "르완다 정부 공공 서비스 디지털화와 전자정부 확대",
        "semantic": "ICT로 행정 서비스의 투명성과 효율성을 높이는 지원 수요",
        "cross_language": "Rwanda digital public services and e-government expansion",
        "policy": "르완다 CPS가 제시한 디지털 행정과 ICT 인적역량 정책방향",
        "negative_country": "우간다",
        "negative_sector": "농림수산",
    },
    {
        "case": "TZA_ENERGY",
        "chunk_id": "CPS-TZA-p19-01",
        "country": "탄자니아",
        "sector": "기술환경에너지",
        "direct": "탄자니아 전력 수요 증가와 송변전 배전망 에너지 인프라 확충",
        "semantic": "낮은 전력 접근성을 개선하고 안정적인 전력 공급망을 확대하는 개발수요",
        "cross_language": "Tanzania electricity access transmission distribution grid and energy infrastructure needs",
        "policy": "탄자니아 CPS의 에너지 정책과 전력 인프라 개발방향",
        "negative_country": "베트남",
        "negative_sector": "공공행정",
    },
    {
        "case": "VNM_ADMIN",
        "chunk_id": "CPS-VNM-p10-01",
        "country": "베트남",
        "sector": "공공행정",
        "direct": "베트남 기획투자부 ODA 주무부처와 사업제안서 승인절차",
        "semantic": "공적개발원조 사업을 총리 승인까지 조정하는 정부 행정체계",
        "cross_language": "Vietnam ODA project proposal approval process led by the Ministry of Planning and Investment",
        "policy": "베트남 CPS의 ODA 시행령과 유상원조 도입절차 정책근거",
        "negative_country": "방글라데시",
        "negative_sector": "교육",
    },
    {
        "case": "BGD_ENERGY",
        "chunk_id": "CPS-BGD-p04-01",
        "country": "방글라데시",
        "sector": "기술환경에너지",
        "direct": "방글라데시 발전소 신설 송전망 개선 에너지 인프라 확충",
        "semantic": "고도성장을 뒷받침할 전력 공급망과 경제 인프라 투자 수요",
        "cross_language": "Bangladesh power plants transmission grid and energy infrastructure investment needs",
        "policy": "방글라데시 제8차 5개년 계획의 에너지 교통 인프라 정책방향",
        "negative_country": "인도네시아",
        "negative_sector": "공공행정",
    },
    {
        "case": "IDN_ADMIN",
        "chunk_id": "CPS-IDN-p16-01",
        "country": "인도네시아",
        "sector": "공공행정",
        "direct": "인도네시아 통합 전자정부 인프라와 정부 행정역량 강화",
        "semantic": "한국의 전자정부 비교우위를 활용해 디지털 공공서비스 체계를 고도화하는 협력",
        "cross_language": "Indonesia integrated e-government infrastructure and public administration capacity",
        "policy": "인도네시아 CPS의 전자정부 인프라와 정부역량 강화 정책방향",
        "negative_country": "네팔",
        "negative_sector": "기술환경에너지",
    },
    {
        "case": "NPL_HEALTH",
        "chunk_id": "CPS-NPL-p16-01",
        "country": "네팔",
        "sector": "보건의료",
        "direct": "네팔 보건의료 전달체계 병상 부족과 의료인력 격차",
        "semantic": "감염병 대응시설과 산간지역 의료인력을 확충해야 하는 수요",
        "cross_language": "Nepal healthcare delivery hospital beds and health workforce shortages",
        "policy": "네팔 CPS의 물관리 보건위생 분야 개발수요 근거",
        "negative_country": "세네갈",
        "negative_sector": "교육",
    },
    {
        "case": "SEN_AGRI",
        "chunk_id": "CPS-SEN-p15-01",
        "country": "세네갈",
        "sector": "농림수산",
        "direct": "세네갈 농업 생산성 농산물 가공과 농촌지역 개발수요",
        "semantic": "수입 의존을 낮추기 위한 농업 가치사슬과 제조 기반 강화",
        "cross_language": "Senegal agricultural productivity agro-processing and rural value chain needs",
        "policy": "세네갈 도약계획의 지역개발 농림수산 분야 수요",
        "negative_country": "우간다",
        "negative_sector": "공공행정",
    },
    {
        "case": "UGA_EDU",
        "chunk_id": "CPS-UGA-p15-01",
        "country": "우간다",
        "sector": "교육",
        "direct": "우간다 교육 접근성과 직업기술교육훈련 품질 향상",
        "semantic": "디지털 전환과 산업수요에 대응하는 교육 품질 및 TVET 역량 강화",
        "cross_language": "Uganda education access TVET quality and digital skills capacity",
        "policy": "우간다 CPS의 교육 접근성 직업기술교육 품질과 디지털 정책방향",
        "negative_country": "페루",
        "negative_sector": "보건의료",
    },
    {
        "case": "PER_CLIMATE",
        "chunk_id": "CPS-PER-p15-01",
        "country": "페루",
        "sector": "기술환경에너지",
        "direct": "페루 순환경제 친환경 투자 기후변화 적응 탄소중립",
        "semantic": "불법 채굴과 벌목으로 훼손된 환경을 복원하고 온실가스를 줄이는 정책",
        "cross_language": "Peru circular economy climate adaptation environmental restoration and carbon neutrality",
        "policy": "페루 국가기본정책의 환경보호와 수자원 안보 목표",
        "negative_country": "필리핀",
        "negative_sector": "공공행정",
    },
    {
        "case": "PHL_AGRI",
        "chunk_id": "CPS-PHL-p20-01",
        "country": "필리핀",
        "sector": "농림수산",
        "direct": "필리핀 농수산업 현대화와 생산성 향상 디지털 관리체계",
        "semantic": "농어업 가치사슬의 경쟁력과 생산성을 높이는 현대화 지원",
        "cross_language": "Philippines agriculture fisheries modernization productivity and digital management",
        "policy": "필리핀 CPS의 농수산업 현대화와 생산성 향상 정책방향",
        "negative_country": "르완다",
        "negative_sector": "보건의료",
    },
]


def normalize(text: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", text.lower())


def split_for(query_id: str) -> str:
    value = int(hashlib.sha256(f"koda-retrieval-v1|{query_id}".encode()).hexdigest()[:8], 16)
    return "dev" if value / 0xFFFFFFFF < 0.30 else "test"


def load_chunks(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {row["Chunk_ID"]: row for row in csv.DictReader(handle)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-dir", required=True)
    args = parser.parse_args()
    pdf_dir = Path(args.pdf_dir)
    chunks = load_chunks(ROOT / "KODA_cps_pdf_chunks.csv")

    gold_rows = []
    validation_rows = []
    variants = [
        ("direct_keyword", "direct", False, False),
        ("semantic_paraphrase", "semantic", False, False),
        ("cross_language", "cross_language", False, False),
        ("policy_alignment", "policy", False, False),
        ("negative_country", "semantic", True, False),
        ("negative_sector", "semantic", False, True),
    ]

    for case in CASES:
        source = chunks[case["chunk_id"]]
        pdf_file = source["PDF_File"]
        pdf_path = pdf_dir / pdf_file
        page_number = int(float(source["Page"]))
        reader = PdfReader(str(pdf_path))
        page_text = reader.pages[page_number - 1].extract_text() or ""
        chunk_norm = normalize(source["Text"])
        page_norm = normalize(page_text)
        match = bool(chunk_norm) and chunk_norm in page_norm

        for query_type, text_key, negative_country, negative_sector in variants:
            query_id = f"GOLD-{case['case']}-{query_type.upper()}"
            country = case["negative_country"] if negative_country else case["country"]
            sector = case["negative_sector"] if negative_sector else case["sector"]
            expected = "" if negative_country or negative_sector else case["chunk_id"]
            row = {
                "query_id": query_id,
                "query_text": case[text_key],
                "query_type": query_type,
                "country": country,
                "sector": sector,
                "expected_chunk_ids": expected,
                "expected_document": pdf_file,
                "expected_pdf_pages": page_number,
                "evidence_class": "Source Evidence",
                "label_source": "CPS original PDF page + committed chunk",
                "label_verified": str(match).lower(),
                "split": split_for(query_id),
                "notes": (
                    f"Grounded in {case['chunk_id']}; metadata mismatch negative"
                    if negative_country or negative_sector
                    else f"Human-authored query grounded in verified {case['chunk_id']}"
                ),
            }
            gold_rows.append(row)
            validation_rows.append(
                {
                    "query_id": query_id,
                    "source_chunk_id": case["chunk_id"],
                    "pdf_file": pdf_file,
                    "pdf_file_page": page_number,
                    "normalized_chunk_chars": len(chunk_norm),
                    "normalized_page_chars": len(page_norm),
                    "chunk_is_page_substring": match,
                    "country_match": source["Country_KR"] == case["country"],
                    "sector_match": source["Sector_Tag"] == case["sector"],
                    "label_verified": match,
                }
            )

    gold_path = ROOT / "benchmarks" / "retrieval_gold_set.csv"
    with gold_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(gold_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(gold_rows)

    validation_path = ROOT / "benchmarks" / "retrieval_gold_set_validation.csv"
    with validation_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(validation_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(validation_rows)

    verified = sum(row["label_verified"] == "true" for row in gold_rows)
    dev = sum(row["split"] == "dev" for row in gold_rows)
    countries = len({row["country"] for row in gold_rows if not row["query_type"].startswith("negative")})
    sectors = len({row["sector"] for row in gold_rows if not row["query_type"].startswith("negative")})
    notes = f"""# Retrieval Gold Set Notes

## Scope

- Internal validation Gold Set, not external expert validation.
- Queries: {len(gold_rows)}
- Verified queries: {verified}
- Positive queries: {sum(bool(row['expected_chunk_ids']) for row in gold_rows)}
- Negative metadata queries: {sum(not bool(row['expected_chunk_ids']) for row in gold_rows)}
- Countries represented by positive labels: {countries}
- Sectors represented by positive labels: {sectors}
- Dev/Test split: {dev}/{len(gold_rows) - dev}

## Label Construction

- Ten CPS chunk IDs were selected before retrieval benchmarking.
- Each selected chunk was compared with the corresponding original PDF file page.
- `label_verified=true` only when normalized committed chunk text was a substring of normalized PDF page text.
- Direct, semantic, cross-language and policy-alignment queries were written from the verified source passage.
- Negative-country and negative-sector queries retain the source meaning but deliberately apply mismatched metadata; they test whether retrieval promotes semantically tempting but metadata-inconsistent evidence.
- Retrieval outputs were not used to create or change labels.

## Interpretation Boundary

- The set is an internal deterministic benchmark, not a representative sample of every CPS question.
- One verified source page per country is expanded into six query forms, so query-level confidence does not equal 60 independent source-page reviews.
- Negative queries are evaluated mainly through mismatch and rejection behavior, not positive Recall.
"""
    (ROOT / "benchmarks" / "retrieval_gold_set_notes.md").write_text(notes, encoding="utf-8")
    print(f"queries={len(gold_rows)} verified={verified} dev={dev} test={len(gold_rows)-dev}")


if __name__ == "__main__":
    main()
