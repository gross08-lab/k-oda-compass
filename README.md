# K-ODA Compass RAG

외교·개발협력 공공데이터를 활용해 국가별 ODA 기회순위, 분야 추천, 정책·리스크 판단, 근거 기반 사업기획서를 생성하는 Evidence-grounded AI 의사결정 지원 서비스입니다.

## Live Links

- Streamlit Cloud: `https://k-oda-compass.streamlit.app`
- GitHub: `https://github.com/gross08-lab/k-oda-compass`
- QR: 앱의 `배포` 탭에서 GitHub/Live Demo QR을 생성할 수 있습니다.

## 핵심 차별점

- RAG형 AI Builder: KOICA/WDI/정책·리스크 근거를 먼저 검색하고, 생성문마다 `[E01]` 형식 citation을 자동 삽입합니다.
- CPS PDF RAG: 국가협력전략 PDF 원문을 page-level chunk로 검색해 정책 정합성 근거를 생성문에 자동 삽입합니다.
- CPS OCR Audit: 27개 CPS PDF, 901개 검색 페이지와 1,100개 유효 청크의 원본 SHA·페이지·재생성 결과를 공개합니다.
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

## 검색 벤치마크

내부 Gold Set은 27개 CPS 국가의 원본 PDF SHA·페이지·정답 청크를 대조한 120개 질의 형식입니다. 고정 분할은 Dev 29 / Test 91이며, label fingerprint는 `c42d43130647b074d5c8e6b7b856aef44009a549f768f17433506792821d0446`입니다. Dev에서만 가중치와 phrase bonus를 선택한 뒤 동결 Test를 한 번 평가했습니다.

최종 국가·분야 필터 결과는 Recall@5 1.000, MRR 0.716, nDCG@5 0.787입니다. Dev가 lexical/embedding 가중치 1.0/0.0을 선택해 운영 기본은 Lexical로 유지합니다. Test 부정 질의 거절은 1/9로 낮으며, 이 내부 벤치마크는 외부 전문가 정확도 검증이 아닙니다.

현재 검증 범위는 27개국 CPS 검색, 저장된 7개 구성점수의 최종 가중합, Local RAG, 5종 출력과 현재 기준선 Citation 구조입니다. 원자료부터 7개 구성점수까지의 상류 계보, Claim-Citation 사람 판정 120쌍, 동일 생성모델 A/B/C 실제 호출과 외부 사용자 파일럿은 완료되지 않았습니다.

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

저장된 7개 구성점수 이후의 Opportunity Score 가중합은 50/50개국, 최대 절대오차 0.005로 재현됩니다. 원자료에서 7개 구성점수를 생성한 상류 코드와 전체 정규화 규칙은 저장소 이력에서 발견되지 않아 전체 상류 재현을 주장하지 않습니다. 세부 상태는 `artifacts/ai_upgrade/score_lineage_report.md`와 `score_lineage_matrix.csv`에 기록했습니다.

## 동일모델 A/B/C

10개 국가·분야 사례의 `GENERIC`, `RAW_EVIDENCE`, `KODA_CONTROLLED` 하네스와 결정론적 평가기는 구현되어 있습니다. 이번 실행환경에는 `OPENAI_API_KEY`가 없어 실제 생성 호출은 0건이며, A/B/C 성능·비용·지연 개선값은 산출하거나 주장하지 않습니다.

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

현재 운영 page cache 기준 CPS PDF 27개·921페이지 중 직접 추출 652페이지, OCR 검색 249페이지, 총 검색 가능 901페이지입니다. 나머지 20페이지는 검색 근거에서 제외됩니다. 이미지 중심 PDF 7개도 OCR-backed 청크로 검색되며, OCR 오인식 가능성은 원문 페이지 대조가 필요합니다.

## 검증 자산

- `artifacts/ai_upgrade/cps_corpus_validation.json`: CPS PDF→페이지→청크 SHA·재현성
- `artifacts/ai_upgrade/retrieval_benchmark_summary.json`: 동결 Test 네 방식 결과
- `artifacts/ai_upgrade/retrieval_benchmark_history.md`: 변경 전후와 보존 범위
- `artifacts/ai_upgrade/citation_audit_summary.json`: 현재 기준선 Citation 구조 감사
- `artifacts/ai_upgrade/score_lineage_audit_summary.json`: 점수 상류 상태
- `artifacts/ai_upgrade/controlled_experiment_summary.json`: A/B/C 실제 실행 수
- `docs/validation_report.md`: 공식 실측 KPI와 한계

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
