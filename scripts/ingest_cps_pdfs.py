from __future__ import annotations

import argparse
import os
import re
from collections import Counter
from pathlib import Path

import pandas as pd
import pdfplumber
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CPS_DIR = Path(os.getenv("KODA_CPS_PDF_DIR", ROOT / "data" / "cps_pdfs"))
DEFAULT_OUTPUT = Path("KODA_cps_pdf_chunks.csv")

CODE_TO_KR = {
    "BGD": "방글라데시",
    "BOL": "볼리비아",
    "COL": "콜롬비아",
    "EGY": "이집트",
    "ETH": "에티오피아",
    "GHA": "가나",
    "IDN": "인도네시아",
    "IND": "인도",
    "KGZ": "키르기스스탄",
    "KHM": "캄보디아",
    "LAO": "라오스",
    "LKA": "스리랑카",
    "MMR": "미얀마",
    "MNG": "몽골",
    "NPL": "네팔",
    "PAK": "파키스탄",
    "PER": "페루",
    "PHL": "필리핀",
    "PRY": "파라과이",
    "RWA": "르완다",
    "SEN": "세네갈",
    "TJK": "타지키스탄",
    "TZA": "탄자니아",
    "UGA": "우간다",
    "UKR": "우크라이나",
    "UZB": "우즈베키스탄",
    "VNM": "베트남",
}

SECTOR_KEYWORDS = {
    "공공행정": ["거버넌스", "공공행정", "행정", "전자정부", "디지털정부", "재정", "세무", "통계", "제도", "공공"],
    "교육": ["교육", "직업훈련", "학교", "대학", "교사", "청년", "역량강화", "TVET", "tvet"],
    "보건의료": ["보건", "의료", "병원", "위생", "감염", "모자보건", "의과", "식수위생"],
    "기술환경에너지": ["에너지", "전력", "기후", "환경", "녹색", "ICT", "ict", "디지털", "기술", "수자원", "물관리"],
    "농림수산": ["농업", "농촌", "수산", "식량", "관개", "농림", "농가", "축산"],
    "긴급구호/취약성": ["취약", "인도적", "난민", "재난", "분쟁", "위기", "재해"],
}


def clean_text(text: str) -> str:
    text = text or ""
    text = text.replace("\x00", " ")
    text = re.sub(r"([가-힣])\1{2,}", r"\1", text)
    text = re.sub(r"([A-Za-z])\1{4,}", r"\1", text)
    text = re.sub(r"-\s*\d+\s*-", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_noisy(text: str) -> bool:
    if len(text) < 120:
        return True
    tokens = re.findall(r"[0-9A-Za-z가-힣]{2,}", text)
    if len(tokens) < 18:
        return True
    unique_ratio = len(set(tokens)) / max(len(tokens), 1)
    dominant_ratio = Counter(tokens).most_common(1)[0][1] / len(tokens)
    return unique_ratio < 0.22 or dominant_ratio > 0.35


def sector_tag(text: str) -> str:
    scores = {}
    for sector, words in SECTOR_KEYWORDS.items():
        scores[sector] = sum(text.count(word) for word in words)
    best_sector, best_score = max(scores.items(), key=lambda item: item[1])
    return best_sector if best_score > 0 else "CPS 정책전략"


def chunk_page_text(text: str, max_chars: int = 1100, overlap: int = 120) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        window = text[start:end]
        cut = max(window.rfind(". "), window.rfind("다. "), window.rfind("; "))
        if cut > 450:
            end = start + cut + 1
            window = text[start:end]
        chunks.append(window.strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [chunk for chunk in chunks if len(chunk) >= 120]


def extract_page_texts(pdf_path: Path) -> list[tuple[int, str, str]]:
    pypdf_reader = PdfReader(str(pdf_path))
    pypdf_texts = [(page.extract_text() or "") for page in pypdf_reader.pages]

    results = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for idx, page in enumerate(pdf.pages):
            plumber_text = page.extract_text() or ""
            pypdf_text = pypdf_texts[idx] if idx < len(pypdf_texts) else ""
            plumber_clean = clean_text(plumber_text)
            pypdf_clean = clean_text(pypdf_text)
            if len(pypdf_clean) > len(plumber_clean) * 1.35:
                chosen = pypdf_clean
                method = "pypdf"
            else:
                chosen = plumber_clean
                method = "pdfplumber"
            results.append((idx + 1, chosen, method))
    return results


def build_chunks(cps_dir: Path) -> pd.DataFrame:
    rows = []
    for pdf_path in sorted(cps_dir.glob("*.pdf")):
        code = pdf_path.stem.upper()
        country = CODE_TO_KR.get(code, code)
        page_texts = extract_page_texts(pdf_path)
        for page_num, text, method in page_texts:
            if is_noisy(text):
                continue
            for idx, chunk in enumerate(chunk_page_text(text), start=1):
                chunk_id = f"CPS-{code}-p{page_num:02d}-{idx:02d}"
                rows.append({
                    "Chunk_ID": chunk_id,
                    "Country_KR": country,
                    "Country_Code": code,
                    "PDF_File": pdf_path.name,
                    "Page": page_num,
                    "Chunk_On_Page": idx,
                    "Sector_Tag": sector_tag(chunk),
                    "Text": chunk,
                    "Text_Length": len(chunk),
                    "Extraction_Method": method,
                    "Citation": f"CPS {country} 국가협력전략 {pdf_path.name} p.{page_num}",
                })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Korean CPS PDF pages into RAG chunks.")
    parser.add_argument("--input", default=str(DEFAULT_CPS_DIR), help="Directory containing CPS PDF files.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output CSV path.")
    args = parser.parse_args()

    cps_dir = Path(args.input).expanduser()
    if not cps_dir.exists():
        raise FileNotFoundError(cps_dir)
    df = build_chunks(cps_dir)
    if df.empty:
        raise RuntimeError("No CPS chunks were extracted.")
    output = Path(args.output)
    df.to_csv(output, index=False, encoding="utf-8-sig")
    print(f"wrote {output.resolve()} rows={len(df)} countries={df['Country_KR'].nunique()}")


if __name__ == "__main__":
    main()
