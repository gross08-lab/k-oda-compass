from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


CASES = [
    ("CG-RWA-TECH", "르완다", "기술환경에너지", "디지털 공공서비스", "CPS-RWA-p26-01"),
    ("CG-TZA-ENERGY", "탄자니아", "기술환경에너지", "전력접근성과 송배전망", "CPS-TZA-p19-01"),
    ("CG-VNM-ADMIN", "베트남", "공공행정", "ODA 행정체계", "CPS-VNM-p10-01"),
    ("CG-BGD-ENERGY", "방글라데시", "기술환경에너지", "전력 인프라", "CPS-BGD-p04-01"),
    ("CG-IDN-ADMIN", "인도네시아", "공공행정", "전자정부", "CPS-IDN-p16-01"),
    ("CG-NPL-HEALTH", "네팔", "보건의료", "보건 전달체계", "CPS-NPL-p16-01"),
    ("CG-SEN-AGRI", "세네갈", "농림수산", "농업 가치사슬", "CPS-SEN-p15-01"),
    ("CG-UGA-EDU", "우간다", "교육", "TVET와 디지털 역량", "CPS-UGA-p15-01"),
    ("CG-PER-CLIMATE", "페루", "기술환경에너지", "기후 적응과 순환경제", "CPS-PER-p15-01"),
    ("CG-PHL-AGRI", "필리핀", "농림수산", "농수산업 현대화", "CPS-PHL-p20-01"),
]


def main() -> None:
    chunks = {}
    with (ROOT / "KODA_cps_pdf_chunks.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            chunks[row["Chunk_ID"]] = row
    master = {}
    with (ROOT / "KODA_master_score_top50_v21.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            master[row["Country_KR"]] = row
    rows = []
    for case_id, country, sector, keywords, chunk_id in CASES:
        chunk = chunks[chunk_id]
        score = master[country]
        rows.append(
            {
                "case_id": case_id,
                "country": country,
                "sector": sector,
                "user_type": "CSO/NGO",
                "scale": "소규모 파일럿",
                "keywords": keywords,
                "opportunity_score": score["K_ODA_Opportunity_Score_V21"],
                "rank": score["Rank_V21"],
                "expected_chunk_id": chunk_id,
                "expected_document": chunk["PDF_File"],
                "expected_page": chunk["Page"],
                "raw_evidence": chunk["Text"],
                "label_basis": "retrieval Gold Set source page verified before controlled experiment",
            }
        )
    path = ROOT / "benchmarks" / "controlled_generation_cases.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"cases={len(rows)}")


if __name__ == "__main__":
    main()
