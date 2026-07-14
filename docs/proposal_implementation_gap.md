# Proposal Implementation Gap Analysis

## 기준선

- Git 기준선: `main` / `12701bd`
- 기준 테스트: Python 3.14.6, 최종 QA 결과는 본 문서 하단과 `docs/validation_report.md` 참조
- 앱 구조: 9개 상위 화면, segmented navigation, 화면별 lazy loading, Local RAG fallback
- 제안서 기준: 2026-07-13 생성 10쪽 최종 제안서

## 핵심 판단

현재 앱은 50개국 점수, 9개 화면, Evidence Pack First, Citation ID, A01-A07 설계가정, 5종 출력과 Local RAG fallback을 갖춘 작동 제품이다. CPS와 검색 검증은 재현 자산을 갖췄지만, 제안서의 MRR·Citation·Score Lineage·A/B/C 수치 일부는 실제값과 불일치한다.

## P0

| ID | 제안서 요구사항 | 기존 구현 상태 | 영향 | 조치 |
|---|---|---|---|---|
| GAP-P0-001 | CPS 27/27 검색·Citation, 유효 청크 1,100개 | **완료**: 27 PDF·921페이지·901 검색페이지·1,100청크 PASS | Top50 교집합은 26/50이며 IND는 Top50 밖 | 코퍼스 검증 JSON을 공식 기준으로 유지 |
| GAP-P0-002 | 확장 Gold Set 120질의, 27개국, Recall@5 0.97·MRR 0.89 | **부분 완료**: 120질의 동결, 실제 Recall@5 1.000·MRR 0.716 | 제안서 MRR 0.89 재현 실패 | 실제 MRR 0.716을 공식값으로 사용 |
| GAP-P0-003 | 동일모델 10사례×3조건 30출력 실측 | **미완료**: API 키 부재, 0/30 실행 | 품질·비용·지연 수치 사용 불가 | 승인된 API 환경에서 동일 설정 실행 필요 |
| GAP-P0-004 | Evidence coverage 94.5%, 미지원 숫자 4건 등 | **미완료**: 실행 출력 0건 | 해당 제안서 수치 재현 불가 | Mock 없이 실제 30출력 후 평가 |
| GAP-P0-005 | 구조 Citation 214/214 전수검사 | **부분 완료**: 현재 기준선 47/47, 제외 ID 0, CPS source chain 3/3 | 214건 모집단 원시자산 없음 | 현재 47건 범위만 명시 |
| GAP-P0-006 | Claim–Citation 120쌍과 kappa 0.81 | **미완료**: 사람 판정 0쌍 | 의미 정확도·kappa 주장 불가 | 두 평가자 원시판정표 필요 |
| GAP-P0-007 | Score Lineage 7/7 VERIFIED | **부분 완료**: 최종 가중합 VERIFIED, 상류 6 PARTIAL·1 UNRESOLVED | raw-to-component 0/7 | 상류 생성 코드·공식 원자료 확보 전 상태 유지 |
| GAP-P0-008 | UI·README 실제 최신값 | **완료**: 검증 JSON lazy load, CPS·검색·Citation·Lineage·A/B/C 상태 표시 | 외부 배포 화면 확인은 별도 | 배포 후 브라우저 회귀검사 |

## P1

| ID | 제안서 요구사항 | 기존 구현 상태 | 영향 | 조치 |
|---|---|---|---|---|
| GAP-P1-001 | 공통 Evidence Pack으로 MD·PDF·Brief·검사 일치 | 공통 result 객체는 있으나 일부 렌더러가 별도 subset 사용 | 화면·다운로드 불일치 위험 | 직렬화 스키마와 스냅샷 테스트 강화 |
| GAP-P1-002 | CPS 국가·분야 직접성 검수 | 키워드·분야 태그 기반 의미 분류 | 배경문장이 직접근거로 승격될 위험 | 정책 직접성 규칙과 검토상태를 별도 필드로 유지 |
| GAP-P1-003 | 26/27 직접근거 연결·1개 추가검토 | 국가별 감사 자산 없음 | 제안서 3쪽 재현 불가 | 국가별 추천 분야·직접근거 교차표 생성 |
| GAP-P1-004 | 입력·설정 해시와 실행별 결과 기록 | 벤치마크·계보 일부에 해시 존재, 사용자 출력 run ID는 제한적 | 기관형 변경관리 기반 약함 | 생성 메타데이터에 data/config/evidence hash 추가 |
| GAP-P1-005 | 214건 구조검사와 120쌍 의미검수 UI 표시 | AI 검증 화면은 기존 내부 통계 중심 | 제안서 검증 구조가 제품에서 보이지 않음 | 검증 manifest를 lazy load하고 Direct/Partial 분리 표시 |
| GAP-P1-006 | 데이터 역할 세 분류의 전역 일관성 | 앱 일부는 정확하나 README·문서에 과거 표현 혼재 | 데이터 직접입력 오해 가능 | 데이터 카탈로그를 기준으로 문구 통일 |
| GAP-P1-007 | 오류·근거 부족 처리 | LLM·임베딩 fallback은 구현, 27개 CPS 미처리 상태는 국가별 안내 | 완전한 27개국 흐름 미검증 | OCR 후 no-hit·잘못된 필터·다운로드 실패 테스트 추가 |

## P2

| ID | 제안서 요구사항 | 기존 구현 상태 | 조치 |
|---|---|---|---|
| GAP-P2-001 | 제안서 용어·숫자·분류 전역 정합 | 여러 세대 문서가 공존 | 검증 manifest 기반 문서 업데이트 |
| GAP-P2-002 | 전문적 UI와 판독 가능한 표·상태 | 기능은 풍부하나 검증 화면이 조밀함 | KPI 축약·상세 expander·모바일 점검 |
| GAP-P2-003 | 재현 가능한 실행·운영 절차 | 스크립트는 있으나 통합 runbook 없음 | one-command QA와 runbook 작성 |
| GAP-P2-004 | 현재와 기관형 확장 경계 | 일부 로드맵 문서가 과거 상태 | 현재·향후 라벨과 금지 표현 검사 |

## 구현 우선순위

1. CPS OCR과 27개국 코퍼스 재구축
2. 120질의 Gold Set과 검색 벤치마크 재현
3. Score Lineage 상류 원자료 조사·복원 가능 범위 확정
4. 통제실험·Citation 감사 자산의 실측 가능성 확보
5. 검증 manifest를 앱·문서의 단일 수치 소스로 연결
6. UI·다운로드·오류처리·E2E 회귀검사

## 금지된 우회

- 제안서 수치에 맞추기 위한 결과 하드코딩
- OCR 없이 7개국을 검색 가능으로 표시
- 실행하지 않은 30개 출력을 실측으로 표시
- Partial Support를 Direct Support로 합산 표기
- 저장된 구성점수의 최종 합산만으로 `7/7 raw-to-component VERIFIED`라고 표기

## 제안서 수치와 실제값

아래 `제안서` 열은 사용자가 제공한 감사 기준본의 주장이다. 이번에 재생성한 `KODA_Compass_Proposal_FINAL_SUBMISSION_1800.pdf`에는 실제 재현값을 반영했으며, MRR 0.89·Citation 214/214·7/7 상류 VERIFIED·30회 실행 주장을 제거했다.

| 항목 | 제안서 | 실제 재현 | 공식 상태 |
|---|---:|---:|---|
| CPS 검색 국가 | 27/27 | 27/27 | VERIFIED |
| 유효 CPS 청크 | 1,100 | 1,100 | VERIFIED |
| Gold 질의 | 120 | 120 | VERIFIED |
| Filtered Recall@5 | 0.97 | 1.000 | VERIFIED actual |
| Filtered MRR | 0.89 | 0.716 | PARTIAL mismatch |
| 구조 Citation | 214/214 | 47/47 current baseline | PARTIAL scope mismatch |
| Claim-Citation 사람 판정 | 120 | 0 | UNRESOLVED |
| Cohen's kappa | 0.81 | 산출 불가 | UNRESOLVED |
| Score 상류 계보 | 7/7 VERIFIED | 0/7 raw-to-component | PARTIAL/UNRESOLVED |
| A/B/C 실제 출력 | 30 | 0 | UNRESOLVED |
