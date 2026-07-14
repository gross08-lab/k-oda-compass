# Proposal Requirement Matrix

## 기준

- 기준 문서: `K-ODA Compass 2026 외교 공공데이터·AI 활용 경진대회 최종 제안서`, 10쪽, 생성일 2026-07-13
- 제품 범위: 공개 Streamlit MVP와 저장소에서 재현 가능한 검증 자산
- 상태 기준: `IMPLEMENTED`, `VERIFIED`, `PARTIAL`, `UNRESOLVED`, `NOT APPLICABLE`
- 원칙: 제안서 수치를 UI에 표시하려면 원본 자산과 재실행 가능한 검증 결과가 모두 존재해야 한다.

## 추적표

| ID | 제안서 페이지 | 원문 또는 핵심 내용 | 요구사항 유형 | 구현 대상 | 현재 상태 | 관련 파일 | 검증 방법 |
|---|---:|---|---|---|---|---|---|
| PR-001 | 1 | 국가·분야 우선순위부터 CPS 원문, Evidence Pack, 사업기획서까지 연결 | 비즈니스 목표 | 전체 사용자 흐름 | PARTIAL | `app.py` | 9개 화면 E2E |
| PR-002 | 1 | 외교·ODA AI 근거 운영체계 | 핵심 가치 | 서비스 정의·문구 | PARTIAL | `app.py`, `README.md` | UI·문서 용어 검색 |
| UI-001 | 1 | 공개 Live Demo와 Open Repository 제공 | 운영 | 배포·저장소 링크 | IMPLEMENTED | `app.py`, `README.md` | URL·QR 확인 |
| MODEL-001 | 1 | 50개국 Opportunity Score·순위 | 정량모델 | 마스터 점수·순위 화면 | IMPLEMENTED | `KODA_master_score_top50_v21.csv`, `app.py` | 50행·순위 재계산 |
| MODEL-002 | 1 | 7개 구성점수 | 정량모델 | 기여도·재현 표 | PARTIAL | `KODA_master_score_top50_v21.csv`, `KODA_v21_score_weights.csv` | 저장 구성점수 합산 |
| DATA-001 | 1 | KOICA 가공 레코드 12,436건, 2019-2024 | 데이터 | KOICA 데이터셋 | IMPLEMENTED | `KODA_project_evidence_top50_2019_2024.csv` | CSV 행 수 |
| RAG-001 | 1 | CPS 27/27 전수 검색·Citation | RAG | OCR 포함 CPS 코퍼스 | VERIFIED | `artifacts/ai_upgrade/cps_corpus_validation.json` | 27 PDF·SHA·페이지·청크 자동검사 |
| QA-001 | 1 | Controlled 근거 연결률 94.5%, 10사례·30출력 | 검증 | A/B/C 실행·평가 자산 | UNRESOLVED | `artifacts/ai_upgrade/controlled_experiment_*` | 실행 상태·원시출력 재계산 |
| QA-002 | 1 | 구조적 Citation 214/214 PASS | 검증 | Citation 전수검사 | PARTIAL | `artifacts/ai_upgrade/citation_audit_summary.json` | 현재 기준선 47/47; 214건 원시범위 없음 |
| QA-003 | 1 | Score Lineage 7/7 VERIFIED | 검증 | 상류 점수 계보 | PARTIAL | `artifacts/ai_upgrade/score_lineage_*` | 최종 합산 VERIFIED; 상류 6 PARTIAL·1 UNRESOLVED |
| FLOW-001 | 1 | 50개국 점수→국가·분야→CPS 원문→Evidence Pack→Citation·가정→5종 출력 | 사용자 시나리오 | 화면 간 상태 유지·Builder | PARTIAL | `app.py` | 단일 세션 E2E |
| AI-001 | 1 | 점수·검색·근거·Citation·설계가정·출력을 분리 | AI 생성 | 공통 구조화 객체 | PARTIAL | `app.py` | 결과 객체·출력 일치 테스트 |
| PR-003 | 2 | 분절 데이터를 검토 가능한 ODA 사업근거로 전환 | 문제 정의 | 개요·문서 | PARTIAL | `app.py`, `README.md` | 문구·워크플로 확인 |
| PR-004 | 2 | 데이터 분절, 원문 추적 단절, 사실·가정 혼합 해결 | 문제 정의 | 개요·근거·Builder | PARTIAL | `app.py` | 3개 문제와 대응 기능 확인 |
| FLOW-002 | 2 | 8단계 수작업을 하나의 근거 흐름으로 축소 | 사용자 시나리오 | 서비스 플로우 | PARTIAL | `app.py` | 8→3 단계 시나리오 E2E |
| USER-001 | 2 | 핵심 사용자는 사전조사 인력이 부족한 중소기업·소셜벤처·중소 NGO/CSO | 대상 사용자 | 사용자 유형·문구 | IMPLEMENTED | `app.py` | Builder 사용자 유형 확인 |
| USER-002 | 2 | 확장 사용자는 지자체·대학·연구기관·컨설턴트·공공기관 | 대상 사용자 | 사용자 유형·로드맵 | PARTIAL | `app.py`, `docs/product_roadmap.md` | 옵션·문서 확인 |
| FLOW-003 | 2 | 분야·지역·규모 입력→Top3·점수·CPS 검토→기획서·근거팩 출력 | 사용자 시나리오 | Builder·탐색 흐름 | PARTIAL | `app.py` | 동일 입력 세션 테스트 |
| UI-002 | 2 | 후보국 점수·기여도·데이터 상태 표시 | UI/UX | 순위·프로필 | IMPLEMENTED | `app.py` | 브라우저 확인 |
| UI-003 | 2 | 협력기반·CPS·WDI·위험을 분리한 분야 검토 | UI/UX | 분야 우선검토 | PARTIAL | `app.py` | 근거 매트릭스 확인 |
| UI-004 | 2 | 27개국 Page·Chunk ID 검색 | UI/UX | 근거·Builder 검색 | VERIFIED | `app.py`, `KODA_cps_pdf_chunks.csv` | 27개국 모두 유효 청크 보유 |
| OUTPUT-001 | 2 | Evidence Pack First·5종 출력 | 출력 | Proposal/Brief/Evidence Pack MD·PDF | IMPLEMENTED | `app.py` | 5개 다운로드 생성 |
| QA-004 | 2 | Citation·Evidence Class·A01-A07로 사실·가정 재분류 | 검증 | Builder QA | PARTIAL | `app.py`, `tests/test_builder_outputs.py` | 품질검사 테스트 |
| DATA-002 | 3 | 구조화 데이터 3개 그룹과 CPS 문서 1개 그룹 | 데이터 | 데이터 카탈로그·UI | PARTIAL | `data/data_manifest.csv`, `app.py` | 분류 일치 확인 |
| DATA-003 | 3 | KOICA ODA 실적 12,436건은 한국 협력기반·사업축적에 사용 | 데이터 | 점수·RAG 역할 | PARTIAL | KOICA CSV, `app.py` | 역할 메타데이터 확인 |
| DATA-004 | 3 | KOICA 통합개발지표 2023-06-14는 개발수요·위험·실행환경에 사용 | 데이터 | 계보·데이터 카탈로그 | PARTIAL | 정책·리스크 CSV | 원자료 출처·열 계보 확인 |
| DATA-005 | 3 | WDI 10개 코드는 국제비교·최신 보조신호 | 데이터 | 프로필·RAG | IMPLEMENTED | `KODA_wdi_latest_top50_long_v2.csv` | 지표코드·최신값 확인 |
| DATA-006 | 3 | CPS 27/27은 정책정합·페이지 Citation에 사용 | 데이터 | OCR 코퍼스 | VERIFIED | CPS PDF·page cache·chunk manifest | 27개 PDF·국가·페이지 확인 |
| DATA-007 | 3 | 현재 핵심, 교차검증·품질시험, 향후 확장을 분리 | 데이터 | UI·README·카탈로그 | PARTIAL | `app.py`, `README.md` | 세 분류 전역 검색 |
| DATA-008 | 3 | 교차검증용 KOICA 국가·분야 통계와 사업정보 Open API를 최종 점수 직접입력으로 표현하지 않음 | 데이터 | 데이터 카탈로그 | PARTIAL | 문서 | 표현 검사 |
| DATA-009 | 3 | 외교부 재외공관·국가정보, KF, 한·아프리카재단은 향후 확장 | NOT APPLICABLE | 로드맵·UI | PARTIAL | `docs/product_roadmap.md` | 현재 기능 오인 문구 검사 |
| RAG-002 | 3 | 27/27 검색·Citation 가능, 유효 청크 1,100개 | RAG | OCR·청킹 | VERIFIED | `artifacts/ai_upgrade/cps_corpus_validation.*` | 유효·빈값·ID·페이지·해시 재계산 |
| RAG-003 | 3 | 26/27 추천 국가·분야와 직접근거 연결, 1개 추가검토 | 검증 | CPS 직접성 평가 | UNRESOLVED | 검증 자산 없음 | 국가별 직접근거 감사 |
| QA-005 | 3 | 확장 Gold Set 120질의 | 검증 | Gold Set | VERIFIED | Gold CSV·freeze JSON·OCR spot-check | 120행·해시·split·정답 ID 검사 |
| DATA-010 | 3 | 공식 출처·기준일·사용 컬럼·변환규칙·SHA-256 계보 | 데이터 계보 | 데이터 매니페스트 | PARTIAL | `data/data_manifest.csv` | 해시·필드 완전성 검사 |
| RISK-001 | 3 | 50개국은 스크리닝, 27개국은 CPS 심층검토, CPS 없음은 탐색 후보 | 한계 | UI 안내 | PARTIAL | `app.py` | 화면 문구 확인 |
| ARCH-001 | 4 | 생성모델과 데이터·점수·검색·Citation 계층 분리 | AI 아키텍처 | 모듈·문서 | PARTIAL | `app.py`, `src/` | 의존성·인터페이스 검토 |
| MODEL-003 | 4 | MCDA 가중치 D25/K20/S15/G10/P15/F10/R5 | 정량모델 | 가중치·수식 | IMPLEMENTED | `KODA_v21_score_weights.csv` | 합계 1.0·재계산 |
| MODEL-004 | 4 | 입력·설정 해시→정합화→결측·극단값→피처→7점수→최종점수→순위 | 데이터 계보 | 점수 파이프라인 | UNRESOLVED | `src/scoring/` | one-command 상류 재실행 |
| QA-006 | 4 | 7/7 구성점수 VERIFIED, 50/50 순위 PASS, 최대 오차 ≤0.005 | 검증 | Score Lineage | UNRESOLVED | lineage artifacts | 재실행·원자료 대조 |
| RAG-004 | 4 | 텍스트·OCR 공통 파이프라인 | RAG | CPS 수집·OCR | VERIFIED | `scripts/ingest_cps_pdfs.py`, `scripts/ocr_cps_pdfs.py` | 캐시 재생성·동일 청크 hash |
| RAG-005 | 4 | 국가·분야 필터 기반 Filtered Hybrid | RAG | 검색 엔진·Builder | VERIFIED | `src/retrieval/`, `app.py` | 필터·결정성·fallback 테스트 |
| RAG-006 | 4 | 임베딩 실패 시 Lexical 자동 전환 | 예외 처리 | 검색 fallback | IMPLEMENTED | `src/retrieval/`, `app.py` | 의존성 제거 테스트 |
| AI-002 | 4 | Local RAG와 선택적 LLM이 동일 Evidence Pack 사용 | AI 생성 | Builder | PARTIAL | `app.py` | 결과 객체 해시·출력 비교 |
| QA-007 | 4 | Filtered Hybrid Recall@5 0.97, MRR 0.89, 120 동결 질의 | 검증 | 검색 벤치마크 | PARTIAL | benchmark artifacts | 실제 Recall@5 1.000·MRR 0.716; 제안 MRR 불일치 |
| QA-008 | 4 | Gold Set은 신청자가 CPS 원문 기준으로 확정 | 검증 | 라벨 감사 | VERIFIED | validation CSV·PDF SHA·spot-check PNG | 원문·페이지·정답 청크 검증 |
| RISK-002 | 4 | 내부 고정 벤치마크이며 외부 전문가 검증이 아님 | 한계 | UI·문서 | PARTIAL | 문서·앱 | 과장 문구 검색 |
| FLOW-004 | 5 | 르완다×기술환경에너지×기업/스타트업×중형 확장사업 대표 흐름 | 사용자 시나리오 | 샘플·세션 상태 | PARTIAL | `app.py`, sample outputs | 동일 조건 E2E |
| MODEL-005 | 5 | 르완다 Opportunity Score 65.28 | 정량모델 | 대표 사례 | IMPLEMENTED | 마스터 CSV | 행 값 확인 |
| UI-005 | 5 | Step 1 르완다 순위·근거상태 | UI/UX | 순위 화면 | IMPLEMENTED | `app.py` | 브라우저 확인 |
| UI-006 | 5 | Step 2 기술환경에너지 분야 근거 | UI/UX | 분야 화면 | PARTIAL | `app.py` | CPS·KOICA·WDI 분리 확인 |
| UI-007 | 5 | Step 3 동일 조건을 Evidence Pack에 전달 | UI/UX | session_state | IMPLEMENTED | `app.py` | 화면 이동 상태 유지 테스트 |
| RAG-007 | 5 | 대표 사례 검색 방식 Filtered Hybrid, 생성 LLM RAG | RAG | Builder 기본·샘플 | PARTIAL | `app.py` | 요청/실효 모드 표시 |
| RISK-003 | 5 | 순위는 자동선정이 아니며 현지 수요·파트너·집행환경 추가검증 | 한계 | UI 안내 | IMPLEMENTED | `app.py` | 문구 확인 |
| AI-003 | 6 | Evidence Pack을 먼저 고정한 뒤 Proposal·Brief·PDF 생성 | AI 생성 | Builder 파이프라인 | IMPLEMENTED | `app.py` | 호출 순서·객체 테스트 |
| FLOW-005 | 6 | Score Context→근거검색→직접성 검수→Evidence Pack→LLM→Citation QA | 사용자 시나리오 | Builder 처리 순서 | PARTIAL | `app.py` | 단계별 런타임 로그·테스트 |
| EVID-001 | 6 | Evidence ID·Class·Directness·Country·Sector·문서·페이지·Chunk·RAG 표시 | Evidence Pack | 구조화 근거 | PARTIAL | `app.py` | 스키마·다운로드 확인 |
| EVID-002 | 6 | 르완다 CPS 직접근거 E01-E04와 페이지·청크 연결 | Citation | 대표 근거 | PARTIAL | CPS CSV, `app.py` | RWA PDF 원문 대조 |
| CIT-001 | 6 | 생성문장 Citation이 Evidence ID와 연결 | Citation | 출력·품질검사 | IMPLEMENTED | `app.py` | 고아·미등록 ID 검사 |
| AI-004 | 6 | A01-A07 설계가정은 근거 사실과 별도 ID로 관리 | AI 생성 | 결과 객체·출력 | IMPLEMENTED | `app.py` | 7개 ID·Class 검사 |
| AI-005 | 6 | 원문·기준연도·가정·추가조사를 사용자가 확인 후 확정 | Human-in-the-loop | UI | PARTIAL | `app.py` | 확인 흐름·안내 점검 |
| OUTPUT-002 | 6 | Proposal MD·Brief MD·Evidence Pack MD·Proposal PDF·Brief PDF | 출력 | 다운로드 | IMPLEMENTED | `app.py` | 5종 생성·열기 |
| QA-009 | 7 | 동일모델·동일사례 10개×3조건, 30개 출력 | 검증 | 통제실험 | UNRESOLVED | experiment outputs | 30개 실행 메타데이터·해시 |
| QA-010 | 7 | A Generic=요청만, B Raw=요청+원문, C Controlled=Score+Evidence Pack+규칙 | 검증 | 프롬프트 | IMPLEMENTED | `prompts/controlled_experiment/` | 입력 통제 테스트 |
| QA-011 | 7 | Evidence coverage A5.2/B65.5/C94.5 | 검증 | 평가 결과 | UNRESOLVED | 실측 결과 없음 | 원시출력 재평가 |
| QA-012 | 7 | 미지원 숫자 주장 A41/B18/C4 | 검증 | 평가 결과 | UNRESOLVED | 실측 결과 없음 | 출력별 주장 집계 |
| QA-013 | 7 | 설계가정 분리 10/40/90% | 검증 | 평가 결과 | UNRESOLVED | 실측 결과 없음 | A-ID 평가 재계산 |
| QA-014 | 7 | Evidence Class 준수 0/30/100% | 검증 | 평가 결과 | UNRESOLVED | 실측 결과 없음 | Class 규칙 평가 |
| QA-015 | 7 | 필수 섹션 완성률 87/93/98% | 검증 | 평가 결과 | UNRESOLVED | 실측 결과 없음 | 섹션 평가 재계산 |
| QA-016 | 7 | 평균 지연 11.4/13.2/16.8초, 토큰 1480/1890/2340, 상대비용 1/1.31/1.62 | 성능 | 통제실험 텔레메트리 | UNRESOLVED | 실측 결과 없음 | API usage·시간 집계 |
| RISK-004 | 7 | 내부 규칙 기반 평가이며 외부 전문가 평가가 아님 | 한계 | UI·문서 | PARTIAL | 문서 | 과장 문구 검사 |
| QA-017 | 8 | Gold Set 27개국·120질의, Recall@5 0.97·MRR 0.89 | 검증 | 검색 벤치마크 | PARTIAL | 120질의 최종 벤치마크 | 질의 수·Recall 충족, 실제 MRR 0.716 |
| QA-018 | 8 | Claim–Citation 120쌍: Direct 101, Partial 15, Context 3, Contradiction 0, Unverifiable 1 | 검증 | 의미 감사 | UNRESOLVED | 원시 감사표 없음 | 120쌍 CSV 합계·원문 대조 |
| QA-019 | 8 | Direct 84.2%와 Direct+Partial 96.7%를 분리 표시 | 검증 | AI 검증 UI·문서 | UNRESOLVED | `app.py` | 수치·분모·범례 확인 |
| QA-020 | 8 | Cohen's kappa 0.81, 불일치 10건 재검토 | 검증 | 평가자 일치도 | UNRESOLVED | 판정 원시표 없음 | 두 평가자 라벨 재계산 |
| QA-021 | 8 | Citation 214건의 ID·Pack·문서·페이지·해시·국가·분야·페이지 텍스트 전수검사 | 검증 | Citation 감사 | PARTIAL | `scripts/audit_citations.py`, citation CSV | 현재 기준선 47건과 CPS 3객체 전수; 214건 범위 없음 |
| QA-022 | 8 | 내부 검증이며 외부 감사·전문가 인증 아님 | 한계 | UI·문서 | PARTIAL | `app.py`, 문서 | 표현 검사 |
| QA-023 | 8 | 검증일 2026-07-13과 표본 범위 표시 | 검증 | 버전·메타데이터 | UNRESOLVED | 검증 자산 | 날짜·해시 확인 |
| BIZ-001 | 9 | 현재 추천이 아니라 데이터·산식·가중치·CPS 버전 변화 원인 관리 | 사업화 | 기관형 아키텍처 | NOT APPLICABLE | `docs/product_roadmap.md` | 현재/향후 구분 확인 |
| BIZ-002 | 9 | 일반 서비스 대비 Claim–Evidence–문서–페이지 추적 | 차별점 | 현재 MVP | PARTIAL | `app.py` | 대표 출력 감사 |
| BIZ-003 | 9 | 입력·설정 해시와 실행별 결과 기록 | 운영 | 계보·실행 메타데이터 | PARTIAL | artifacts, `app.py` | 해시·run ID 확인 |
| BIZ-004 | 9 | 구성점수 변화 분해, 검토이력·승인·감사로그는 기관형 확장 | NOT APPLICABLE | 로드맵 | IMPLEMENTED | 문서 | 현재 기능 오인 표현 없음 |
| BIZ-005 | 9 | 공개 MVP는 50개국·27 CPS·Evidence Pack·5종 출력 | 사업화 | 제품 범위 | IMPLEMENTED | `app.py`, CPS validation, Builder tests | 로컬 제품 범위 검증 |
| BIZ-006 | 9 | 향후 조직계정·권한·비공개 저장·정기갱신·백업·SLA | NOT APPLICABLE | 로드맵 | IMPLEMENTED | 문서 | 현재/향후 라벨 확인 |
| BIZ-007 | 9 | 기본 탐색은 무료, 기관별 운영기능은 파일럿 후 유료 워크스페이스 | 사업화 | 로드맵 | PARTIAL | `docs/product_roadmap.md` | 사업화 문구 확인 |
| ROAD-001 | 10 | 0-30일 CPS·데이터 회귀검사 월 1회, 점수·순위 100% PASS, 민감도 5종 | 운영 | 90일 계획 | NOT APPLICABLE | 문서 | KPI 현재/계획 구분 |
| ROAD-002 | 10 | 31-60일 전문가 5명, Citation 사례 30건, 수정률·일치도 측정 | 검증 | 90일 계획 | NOT APPLICABLE | 문서 | 외부검증 완료 오인 없음 |
| ROAD-003 | 10 | 61-90일 조직 10개, 과업 30건, 시간·성공률·수정률 측정 | 사용자 검증 | 90일 계획 | NOT APPLICABLE | 문서 | 실증 전 표현 확인 |
| SAFE-001 | 10 | Human-in-the-loop, 최종 판단은 사용자 | 책임 AI | UI·문서 | IMPLEMENTED | `app.py`, 문서 | 안내 문구 확인 |
| SAFE-002 | 10 | 자동 정책결정 금지, 초기 우선검토 도구 | 책임 AI | UI·문서 | IMPLEMENTED | `app.py` | 과장·자동선정 문구 검색 |
| SAFE-003 | 10 | 사실·가정 분리, 오류·한계 공개 | 책임 AI | Builder·검증 UI | PARTIAL | `app.py` | E/A ID·PASS/REVIEW 확인 |
| SAFE-004 | 10 | ESG: 기후·환경 기회, 중소조직 접근성, 투명성과 책임성 | 사회적 가치 | 개요·로드맵 | PARTIAL | 문서 | 제안서 문구 일치 |
| OPER-001 | 10 | 공개 서비스에서 27 CPS·점수·Evidence Pack·5종 출력 | 운영 | Streamlit Cloud | PARTIAL | `app.py` | 배포 URL E2E |
| OPER-002 | 10 | 공개 저장소에 코드·Gold Set·실험·감사·검증 자산 제공 | 운영 | GitHub 저장소 | PARTIAL | repository | 자산 존재·재실행 확인 |
| PR-005 | 10 | 생성형 AI 대시보드가 아니라 재현·검증·감사 가능한 공공 AI 근거 운영체계 | 핵심 차별점 | 전체 제품 | PARTIAL | 전체 | 추적표 충족률·E2E |

## 현재 요구사항 집계

이 표는 2026-07-14 최종 로컬 검증 기준이다. `VERIFIED`는 저장소에서 재실행 가능한 범위, `IMPLEMENTED`는 기능은 있으나 외부 배포·사용자 검증까지 완료하지 않은 범위다. 제안서 수치와 실제값이 다르면 `PARTIAL`로 유지한다.

- VERIFIED 8
- IMPLEMENTED 23
- PARTIAL 45
- UNRESOLVED 15
- NOT APPLICABLE 4
