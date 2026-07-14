from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = (
    "gpt-5.2",
    "gpt-5.5",
    "gpt-5.6 Sol",
    "1-page",
    "one-page",
    "Citation 정확도 100%",
    "고유 사업 12,436",
    "CPS 27개국 전체 검색 가능",
    "저장 국가·분야 분석 테이블",
    "원재료·외부 데이터",
    "범용 최신 LLM 단독",
    "쓰지않고",
    "/Users/",
    "/home/",
    "serviceKey 실제값",
    "github token",
    "20개국 검색",
    "19/50",
    "806개",
    "60개 질의",
    "38 PASS",
    "214/214",
    "MRR 0.89",
)

REQUIRED = (
    "1,100개",
    "26/50",
    "29 / 91",
    "54 PASS",
    "47 / 47",
    "17 / 17",
    "11.59ms",
    "0.716",
)


def annotation_urls(reader: PdfReader) -> list[str]:
    urls = []
    for page in reader.pages:
        for annotation_ref in page.get("/Annots", []):
            annotation = annotation_ref.get_object()
            action = annotation.get("/A")
            if action and action.get("/URI"):
                urls.append(str(action["/URI"]))
    return urls


def contact_sheet(paths: list[Path], output: Path) -> None:
    thumbs = []
    for path in paths:
        image = Image.open(path).convert("RGB")
        image.thumbnail((420, 594), Image.Resampling.LANCZOS)
        thumbs.append((path.name, image.copy()))
    width = 900
    height = 5 * 650 + 40
    sheet = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (name, image) in enumerate(thumbs):
        column = index % 2
        row = index // 2
        x = 20 + column * 440
        y = 20 + row * 650
        sheet.paste(image, (x, y + 24))
        draw.text((x, y), name, fill="#173F67")
    sheet.save(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pdf",
        type=Path,
        default=ROOT / "artifacts" / "proposal" / "final_submission_ai_upgrade" / "KODA_Compass_Proposal_FINAL_SUBMISSION_1800.pdf",
    )
    parser.add_argument(
        "--rendered",
        type=Path,
        default=ROOT / "artifacts" / "proposal" / "final_submission_ai_upgrade" / "rendered_0714",
    )
    args = parser.parse_args()
    reader = PdfReader(str(args.pdf))
    page_texts = [page.extract_text() or "" for page in reader.pages]
    all_text = "\n".join(page_texts)
    rendered = sorted(args.rendered.glob("page-*.png"))
    image_checks = []
    for path in rendered:
        image = Image.open(path).convert("L")
        extrema = image.getextrema()
        image_checks.append({"file": path.name, "extrema": extrema, "nonblank": extrema[0] < 245})
    urls = annotation_urls(reader)
    forbidden_hits = {term: all_text.count(term) for term in FORBIDDEN if term in all_text}
    required_hits = {term: all_text.count(term) for term in REQUIRED}
    secret_hits = re.findall(r"(?:sk-[A-Za-z0-9_-]{12,}|OPENAI_API_KEY\s*=\s*\S+)", all_text)
    sizes = []
    for page in reader.pages:
        sizes.append((round(float(page.mediabox.width), 2), round(float(page.mediabox.height), 2)))
    output_dir = args.pdf.parent
    contact_sheet(rendered, output_dir / "KODA_Compass_Contact_Sheet_1800.png")
    payload = {
        "validation_date": "2026-07-14",
        "pdf": args.pdf.name,
        "bytes": args.pdf.stat().st_size,
        "sha256": hashlib.sha256(args.pdf.read_bytes()).hexdigest(),
        "pages": len(reader.pages),
        "page_sizes": sizes,
        "all_a4": all(abs(width - 595.28) < 1 and abs(height - 841.89) < 1 for width, height in sizes),
        "page_text_characters": [len(text.strip()) for text in page_texts],
        "rendered_pages": len(rendered),
        "rendered_nonblank": all(item["nonblank"] for item in image_checks),
        "image_checks": image_checks,
        "annotation_urls": sorted(set(urls)),
        "live_demo_link_present": "https://k-oda-compass.streamlit.app" in urls,
        "github_link_present": "https://github.com/gross08-lab/k-oda-compass" in urls,
        "forbidden_hits": forbidden_hits,
        "required_hits": required_hits,
        "required_metrics_present": all(required_hits.values()),
        "secret_hits": secret_hits,
        "qr_image_decode": "BLOCKED_BY_ENVIRONMENT",
    }
    (output_dir / "qa_automated_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
