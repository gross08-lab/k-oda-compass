# K-ODA Compass RAG 최종 제출 브리프

## 한 줄 정의

K-ODA Compass RAG는 외교·개발협력 공공데이터를 국가 선정, 분야 추천, CPS 정책정합성 검토, 근거 기반 사업기획서 생성까지 연결하는 Evidence-grounded AI ODA 기획 지원 서비스입니다.

## 왜 수상권인가

| 심사 관점 | 제출물의 답 |
|---|---|
| 공공데이터 활용성 | KOICA 2019-2024 사업 12,436건, WDI 500행, CPS PDF 806개 chunk, 27개 CPS OCR 감사, 정책·리스크 proxy, 분야 포트폴리오를 결합 |
| AI 혁신성 | 단순 챗봇이 아니라 CPS PDF/KOICA/WDI/정책근거를 먼저 검색한 뒤 citation이 붙은 사업기획서를 생성하는 RAG형 AI Builder |
| 서비스 완성도 | Streamlit 앱, 국가 Top50 순위, 국가 프로필, AI Builder, AI검증, 심사모드, 배포/QR 탭까지 구현 |
| 검증 가능성 | 점수모델 재현, RAG 코퍼스 통계, CPS 텍스트/OCR 커버리지, 민감도 분석, Model Card/Data Card/Test를 함께 제공 |
| 실사용성 | CSO, 지자체, 기업, 정책담당자가 국가·분야·근거·위험요인·KPI·1-page brief를 바로 확보 |
| 확산성 | GitHub push, Streamlit Cloud, Docker, QR, 샘플 산출물, 발표 스크립트까지 제출 패키지화 |

## 핵심 수치

- 분석 대상: ODA 협력 후보 50개국
- KOICA 사업 근거: 12,436건
- WDI 최신 지표: 500행, 10개 핵심 지표
- CPS PDF 근거: 20개국, 806개 page-level chunk
- CPS OCR 감사: 27개 PDF, 663/921 텍스트 레이어 페이지, 7개 이미지형 PDF OCR 대상
- 분야 포트폴리오: 669개 국가·분야 조합
- 샘플 결과물: 탄자니아, 베트남, 르완다 3개 시나리오의 proposal, brief, evidence pack, PDF

## 대표 시연 시나리오

1. `AI Builder`에서 `CSO 탄자니아 공공행정` 시나리오를 선택합니다.
2. `RAG형 AI 사업기획서 생성`을 실행합니다.
3. 생성문 안의 `[E01]` citation을 눌러 CPS PDF, KOICA, WDI, 정책·리스크 근거를 확인합니다.
4. `AI검증`에서 점수 재현성, RAG 문서 수, CPS PDF 커버리지, OCR 대상 페이지, 민감도 분석을 확인합니다.
5. `1-page Brief`, `Evidence Pack`, `PDF`를 내려받아 실제 공모·사업기획 제출물 형태로 확인합니다.

## 압도적 차별점

K-ODA Compass RAG는 “ODA 데이터 대시보드”에서 멈추지 않습니다. 국가 추천의 이유, 정책 문서 근거, 과거 KOICA 사업 맥락, 개발수요 지표, 리스크 보완 논리를 한 번의 흐름으로 묶어 실제 제출 가능한 사업기획 초안까지 생성합니다. AI 기능은 환각을 줄이기 위해 Evidence Pack을 먼저 고정하고, 모든 핵심 문장에 근거 ID를 남깁니다.

## 남은 배포 액션

- GitHub 저장소 URL을 생성한 뒤 이 폴더를 push합니다.
- Streamlit Cloud에서 `app.py`를 entrypoint로 배포합니다.
- 배포 URL을 README, 앱의 `배포` 탭, 발표자료, QR에 반영합니다.
- OpenAI API 키가 있으면 Streamlit Secrets에 `OPENAI_API_KEY`, `OPENAI_MODEL`을 추가합니다.

## 최종 포지션

이 제출물은 “아이디어”가 아니라 작동하는 정책 AI microservice입니다. 공공데이터 융합, RAG형 AI, citation, 검증, 샘플 산출물, 배포 설계가 모두 들어 있어 외교 공공데이터 활용성과 AI 서비스 완성도를 동시에 보여줄 수 있습니다.
