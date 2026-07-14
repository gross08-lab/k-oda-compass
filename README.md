# K-ODA Compass RAG

외교·개발협력 공공데이터를 활용해 국가별 ODA 기회순위, 분야 추천, 정책·리스크 판단, 근거 기반 사업기획서를 생성하는 Evidence-grounded AI 의사결정 지원 서비스입니다.

## Live Links

- Streamlit Cloud: `https://k-oda-compass.streamlit.app`
- GitHub: `https://github.com/gross08-lab/k-oda-compass`
- QR: 앱의 `배포` 탭에서 GitHub/Live Demo QR을 생성할 수 있습니다.

## 핵심 차별점

- RAG형 AI Builder: KOICA/WDI/정책·리스크 근거를 먼저 검색하고, 생성문마다 `[E01]` 형식 citation을 자동 삽입합니다.
- CPS PDF RAG: 국가협력전략 PDF 원문을 page-level chunk로 검색해 정책 정합성 근거를 생성문에 자동 삽입합니다.
- CPS OCR Audit: 원본 SHA·페이지·재생성 계보를 공개하며, 현재 범위 값은 canonical public manifest에서 확인합니다.
- 실제 LLM 연동: `OPENAI_API_KEY`가 있으면 OpenAI Responses API로 근거팩 기반 문장을 고도화합니다.
- 데모 안정성: API 키가 없어도 로컬 RAG 생성기로 동일한 Evidence Pack 기반 결과를 생성합니다.
- 설명 가능한 추천: 국가별 점수 기여도, 정책·리스크 proxy, 민감도 분석을 앱 안에서 검증합니다.
- 검증된 검색 선택: lexical, embedding, hybrid, 국가·분야 필터 hybrid를 같은 내부 Gold Set에서 비교하며, 동결 test 결과가 가장 안정적인 lexical을 운영 기본값으로 유지합니다.
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

## 서류평가 공개 KPI

앱 첫 화면은 `artifacts/screening/canonical_public_kpis.json`을 로드합니다. README는 별도 수치표를 유지하지 않고 이 manifest만 공개 기준으로 안내합니다.

| 공개 검증 항목 | canonical manifest 필드 |
|---|---|
| CPS 원문 검색 | `cps` |
| 검색 Gold Set·운영 평가 | `retrieval` |
| 점수·순위 재현 | `score_reproduction` |
| 근거형 출력·가정 분리 | `features` |
| API 없는 기본 경로 | `features.local_rag_without_api_key` |
| 자동 QA | `qa` |

제출 이후의 검색 순위 세부지표, baseline 출력 Citation 발생 횟수, 원자료부터 구성점수까지의 상류 계보 복구, 외부모델 통제실험 기록은 평가시점과 모집단이 다른 엔지니어링 진단입니다. 이를 제출 대조 KPI의 대체값으로 병합하지 않으며, 상세 진단 덤프는 공개 제품 문서에서 제외합니다.

## 검색 벤치마크

내부 Gold Set은 원본 PDF SHA·페이지·정답 청크를 연결하고 Dev/Test 분할과 label fingerprint를 동결합니다. 현재 질의 수, 분할, fingerprint와 운영 평가값은 canonical public manifest의 `retrieval` 객체에서만 확인합니다.

운영 경로는 국가·분야 필터를 적용하고, 현재 배포 기본 검색은 안정적인 lexical 방식입니다. 내부 벤치마크는 외부기관 인증이나 현지 사업수요 검증을 의미하지 않습니다.

현재 공개 검증 범위의 정의와 분모는 canonical public manifest에 기록합니다. 같은 이름의 지표라도 평가시점이나 모집단이 다른 제출 후 진단값은 공개 KPI와 혼용하지 않습니다.

선택형 임베딩 실험 환경은 Streamlit 배포 의존성과 분리되어 있습니다.

```bash
python3 -m venv .venv-ai-upgrade
.venv-ai-upgrade/bin/pip install -r requirements-ai-upgrade.txt
PYTHONPATH=. .venv-ai-upgrade/bin/python scripts/build_embedding_index.py
PYTHONPATH=. HF_HUB_OFFLINE=1 .venv-ai-upgrade/bin/python scripts/run_retrieval_benchmark.py --phase dev
# Dev 선택값을 config/retrieval.yaml에 고정한 뒤 Test는 한 번만 실행
PYTHONPATH=. HF_HUB_OFFLINE=1 .venv-ai-upgrade/bin/python scripts/run_retrieval_benchmark.py --phase final
```

모델 또는 인덱스를 사용할 수 없으면 앱은 이유를 표시하고 lexical 검색으로 전환합니다. 임베딩 모델 파일과 cache는 Git에 포함하지 않습니다.

## 점수 계보

공개 점수 재현 KPI의 범위는 저장된 구성점수에서 Opportunity Score와 최종 순위를 다시 계산하는 단계입니다. 현재 범위와 결과는 canonical public manifest의 `score_reproduction` 객체에서만 확인합니다. 원자료에서 구성점수까지의 제출 후 계보 복구 기록은 별도 엔지니어링 진단이며 공개 KPI와 합산하지 않습니다.

## 제출 후 엔지니어링 진단

재현 스크립트와 진단 범위 요약은 `artifacts/ai_upgrade/`에서 관리합니다. 상세 로컬 진단값은 공개 KPI가 아니며, `canonical_public_kpis.json`에 포함되지 않은 값은 Live Demo의 제출 대조 성능으로 주장하지 않습니다.

## LLM 모드

선택적 외부 LLM 경로는 환경변수로 설정하며, 현재 검증 기준선은 Local RAG입니다. LLM RAG 모드를 사용하려면 환경변수 또는 Streamlit Secrets에 아래 값을 넣습니다.

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

- `FINAL_SUBMISSION_BRIEF.md`: 심사위원용 요약 원문
- `FINAL_SUBMISSION_BRIEF.pdf`: 바로 열어볼 수 있는 제출 브리프
- `FINAL_PITCH_DECK_KODA_COMPASS_RAG.pptx`: 8장 발표용 피치덱
- `docs/cps_ocr_coverage.md`: CPS PDF OCR 커버리지 리포트
- `docs/llm_verification_result.md`: 실제 LLM 호출 검증 결과 또는 API 키 대기 리포트
- `docs/final_deployment_handoff.md`: GitHub/Streamlit/QR 마감 절차
- `docs/project_completion_walkthrough.md`: 실제 앱 스크린샷 기반 완성 과정 설명

## CPS PDF 재생성

PDF 원본 디렉터리를 별도로 확보한 환경에서:

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

현재 운영 page cache의 PDF·페이지·OCR·청크 범위는 canonical public manifest의 `cps` 객체에서 확인합니다. 검색 불가능한 페이지는 근거에서 제외하며 OCR-backed 근거는 원문 페이지 대조가 필요합니다.

## 공개 검증 파일

공개 KPI는 아래 단일 manifest만 사용합니다. 제출 후 엔지니어링 기록은 평가시점과 모집단이 다를 수 있으며 Live Demo KPI로 사용하지 않습니다.

- `artifacts/screening/canonical_public_kpis.json`: 정의·분모·출처·검증일
- `docs/validation_report.md`: 공개 검증 범위와 재현 명령
- `artifacts/ai_upgrade/README.md`: 제출 후 엔지니어링 자산의 범위 구분

## LLM 검증

실제 OpenAI 호출 검증 리포트는 다음 명령으로 생성합니다.

```bash
python3 scripts/verify_llm_call.py
```

`OPENAI_API_KEY`가 없으면 `docs/llm_verification_result.md`에 pending 리포트를 남기고, 키가 있으면 실제 Responses API 호출 결과와 citation check를 기록합니다.

## 배포

1. 공개 저장소 `https://github.com/gross08-lab/k-oda-compass`의 `main` 브랜치 확인
2. Streamlit Cloud의 `app.py` 배포 상태 확인
3. 선택적 LLM 모드가 필요하면 Secrets에 `OPENAI_API_KEY` 추가
4. `https://k-oda-compass.streamlit.app`에서 Local RAG fallback과 다운로드 경로 확인

## 한계와 안전장치

- 본 서비스는 최종 사업선정 도구가 아니라 예비기획·의사결정 보조도구입니다.
- 정책·리스크는 공개자료 기반 proxy이며, CPS 최신성·현지수요·파트너·예산 타당성은 별도 검증해야 합니다.
- LLM 모드는 Evidence Pack 안의 근거만 사용하도록 prompt를 제한하고, 생성 결과에 citation ID를 남깁니다.
