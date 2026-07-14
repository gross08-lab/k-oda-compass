# K-ODA Compass RAG

> Historical baseline snapshot. Counts and validation statements below describe the pre-upgrade state and are retained for before/after comparison. Current verified metrics are in `docs/validation_report.md` and `artifacts/ai_upgrade/cps_corpus_validation.json`.

외교·개발협력 공공데이터를 활용해 국가별 ODA 기회순위, 분야 추천, 정책·리스크 판단, 근거 기반 사업기획서를 생성하는 Evidence-grounded AI 의사결정 지원 서비스입니다.

## Live Links

- Streamlit Cloud: `https://k-oda-compass.streamlit.app`
- GitHub: `https://github.com/gross08-lab/k-oda-compass`
- QR: 앱의 `배포` 탭에서 GitHub/Live Demo QR을 생성할 수 있습니다.

## 핵심 차별점

- RAG형 AI Builder: KOICA/WDI/정책·리스크 근거를 먼저 검색하고, 생성문마다 `[E01]` 형식 citation을 자동 삽입합니다.
- CPS PDF RAG: 국가협력전략 PDF 원문을 page-level chunk로 검색해 정책 정합성 근거를 생성문에 자동 삽입합니다.
- CPS OCR Audit: 27개 CPS PDF의 텍스트 레이어와 OCR 대상 페이지를 별도 리포트로 공개해 근거 커버리지를 검증합니다.
- 실제 LLM 연동: `OPENAI_API_KEY`가 있으면 OpenAI Responses API로 근거팩 기반 문장을 고도화합니다.
- 데모 안정성: API 키가 없어도 로컬 RAG 생성기로 동일한 Evidence Pack 기반 결과를 생성합니다.
- 설명 가능한 추천: 국가별 점수 기여도, 정책·리스크 proxy, 민감도 분석을 앱 안에서 검증합니다.
- 제출 완성도: 사업기획서 Markdown, Brief Markdown, Evidence Pack, Proposal PDF, Brief PDF, QR 배포 패널을 제공합니다.
- 심사모드: 평가축 대응표, 90초 발표 흐름, 경쟁작 대비 포지션, 제출 체크리스트를 앱 안에서 바로 보여줍니다.

## 데이터

- KOICA ODA 사업근거 2019~2024
- World Bank WDI 2019~2025 최신값
- KOICA 협력국 통합 개발지표 기반 정책·리스크 proxy
- CPS(kor) 국가협력전략 PDF 추출 chunk
- CPS PDF OCR 커버리지 감사표
- K-ODA Compass v2.1 점수모델 및 가중치

## 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

## LLM 모드

로컬 RAG 모드는 별도 설정 없이 동작합니다. LLM RAG 모드를 사용하려면 환경변수 또는 Streamlit Secrets에 아래 값을 넣습니다.

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="<OPTIONAL_MODEL_NAME>"
```

Streamlit Cloud에서는 `App settings > Secrets`에 다음 형식으로 입력합니다.

```toml
OPENAI_API_KEY = "..."
OPENAI_MODEL = "<OPTIONAL_MODEL_NAME>"
```

## 추천 시연 시나리오

1. `AI Builder` 탭에서 `CSO 탄자니아 공공행정` 선택
2. `RAG형 AI 사업기획서 생성` 클릭
3. `근거 Citation` 탭에서 KOICA/WDI 근거 ID 확인
4. CPS PDF 원문 근거가 포함된 citation 확인
5. `점수 기여도` 탭에서 추천 사유 설명
6. `Brief MD`, `Evidence Pack MD`, `Proposal PDF`, `Brief PDF` 다운로드
7. `AI검증` 탭에서 RAG 문서 수, CPS 커버리지, 점수 재현성, 민감도 분석 확인
8. `심사모드` 탭에서 심사기준 대응표 확인
9. `배포` 탭에서 GitHub/Streamlit URL QR 생성

## 샘플 산출물

`sample_outputs/`에는 발표 fallback용 샘플이 포함되어 있습니다.

- 탄자니아 공공행정 CSO 시나리오
- 베트남 디지털정부 지자체 시나리오
- 르완다 ICT·에너지 기업 시나리오

각 시나리오는 Proposal MD, Brief MD, Evidence Pack MD, Proposal PDF, Brief PDF를 포함합니다.

`sample_outputs/case_studies/`에는 실제 서비스 납품 사례처럼 보이는 3페이지 case study PDF가 추가로 포함되어 있습니다.

- 탄자니아 공공행정 CSO case study
- 베트남 디지털정부 지자체 case study
- 르완다 ICT·에너지 기업 case study

## 최종 제출 보조자료

- `FINAL_SUBMISSION_BRIEF.md`: 심사위원용 1페이지 요약 원문
- `FINAL_SUBMISSION_BRIEF.pdf`: 바로 열어볼 수 있는 1페이지 제출 브리프
- `FINAL_PITCH_DECK_KODA_COMPASS_RAG.pptx`: 8장 발표용 피치덱
- `docs/cps_ocr_coverage.md`: CPS PDF OCR 커버리지 리포트
- `docs/llm_verification_result.md`: 실제 LLM 호출 검증 결과 또는 API 키 대기 리포트
- `docs/final_deployment_handoff.md`: GitHub/Streamlit/QR 마감 절차
- `docs/project_completion_walkthrough.md`: 실제 앱 스크린샷 기반 완성 과정 설명

## CPS PDF 재생성

PDF 원본 디렉터리를 지정할 때:

```bash
python3 scripts/ingest_cps_pdfs.py --input "<CPS_PDF_DIRECTORY>" --output KODA_cps_pdf_chunks.csv
```

OCR 커버리지를 갱신하려면:

```bash
python3 scripts/cps_ocr_coverage.py --input "<CPS_PDF_DIRECTORY>"
```

Tesseract Korean OCR이 설치된 환경에서 이미지형 PDF까지 재추출하려면:

```bash
python3 scripts/ocr_cps_pdfs.py --input "<CPS_PDF_DIRECTORY>" --output KODA_cps_pdf_chunks.csv
```

샘플 산출물을 재생성하려면:

```bash
python3 scripts/generate_submission_samples.py
python3 scripts/generate_case_study_pdfs.py
```

이 baseline 생성 당시 감사에서는 CPS PDF 27개의 텍스트 레이어를 663/921페이지로 기록했고, COL/GHA/KHM/MMR/MNG/PAK/PRY 7개 PDF를 이미지형 OCR 보강 대상으로 분류했습니다. 이 문단은 역사적 비교용이며 현재 운영 수치로 사용하지 않습니다. 현재 검증값은 직접 추출 652페이지, OCR 검색 249페이지, 총 검색 가능 901페이지입니다.

## LLM 검증

실제 OpenAI 호출 검증 리포트는 다음 명령으로 생성합니다.

```bash
python3 scripts/verify_llm_call.py
```

`OPENAI_API_KEY`가 없으면 `docs/llm_verification_result.md`에 pending 리포트를 남기고, 키가 있으면 실제 Responses API 호출 결과와 citation check를 기록합니다.

## 배포

1. GitHub repository 생성
2. 이 폴더 전체를 push
3. Streamlit Cloud에서 `app.py`를 entrypoint로 배포
4. Secrets에 `OPENAI_API_KEY` 추가
5. 배포 URL을 README, 발표자료, 앱의 `배포` 탭에 반영

## 한계와 안전장치

- 본 서비스는 최종 사업선정 도구가 아니라 예비기획·의사결정 보조도구입니다.
- 정책·리스크는 공개자료 기반 proxy이며, CPS 최신성·현지수요·파트너·예산 타당성은 별도 검증해야 합니다.
- LLM 모드는 Evidence Pack 안의 근거만 사용하도록 prompt를 제한하고, 생성 결과에 citation ID를 남깁니다.
