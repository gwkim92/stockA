# 검증 기록

- 성과 SQL: 임시 PostgreSQL 17에서 과거 유니버스, 휴장일 27일 성과, 기존 row 보존, 중복 실행, 5일 관측 불일치 3개 검사 통과.
- Python 연관 254개 통과. 전체 discovery에서 발견한 기존 환경 테스트 fixture의 TossInvest 필수값 누락을 가짜 값으로 보완하고 비밀값 비노출 검사를 유지했다. 실제 환경·인증 값은 변경하지 않았다.
- 웹 단위 523개, 타입 검사, production build 통과. 후속 공유 리서치 출처 UI의 CI build와 운영 화면 검증도 아래와 같이 완료했다.
- 실제 DB 읽기 전용 성과 사전 점검: batch×horizon 66개, 미처리 추천×기간 1,009개. 기존 허용 범위 밖 관측 0개. 실제 기간 분포와 원본 크기 점검은 ignored `output/purpose-fit-recovery-20260911/`에 저장했다.
- 실제 입력 크기 점검: 테마 12개와 NVDA/AAPL/ARM 3개 모두 상한 내 선택. 기업 입력에서 큰 중첩 가치평가가 다른 자료를 밀어내지 않도록 축소 시 개별 record 상한을 추가했다. 후속 확인에서 제외 건수를 검증한다.
- 운영 자료를 읽는 로컬 Chrome: NVDA 대체 보고서/형식 확인/내용 검토 미기록/입력 원천/6일 전 가격과 7일 기준 표시 확인. 기존 저장 보고서는 재생성 전이며 실제 AI 보고서로 표현하지 않는다.

전체 Python discovery 1,620개 실행 통과(환경 의존 16개 skip). 별도 PostgreSQL 3개 및 로컬 HTTP 서버 22개도 통과했다. PR의 과거 화면 갤러리 파일 끝 공백 검사가 실패해 해당 공백만 제거했다.

초기 검증 당시 배포 전이었으며, 승인 후 실행 증거를 아래에 추가했다.

## 최종 로컬 실자료 확인

- NVDA recommendation-1468 목록/상세 decision_boundary 완전 일치: paper_validation_pending, 가상 검증 입력 true, 성과 미측정, 주문 false.
- 실제 테마 API의 market_breadth=1.0, fundamental_quality=null, valuation_score=null 확인. 목록 projection에서 누락됐던 새 필드를 추가하고 회귀 테스트를 보완했다.
- Chrome 1440×1000/390×844에서 기업 화면·재무 탭·입력 원천 발췌·Escape 후 입력 문서 버튼으로 복귀 확인. 모바일 문서 너비 390px, 가로 넘침 없음. 관련 캡처는 output/playwright/purpose-fit-*.png.
- 원천 첫 조회 오류는 기존 공유 SSH 연결 정체와 함께 발생했다. 서버 메모리 가용 1,089MB, load 0.00, API ready/web 200을 새 SSH 연결로 확인했다. 산출물 전송을 별도 연결로 분리하고 기존 13309 터널을 동일 포트/키/대상으로 다시 연결했다. 이후 13309=200 및 원천 재조회가 성공했다.

## CI와 통합

- PR #52: https://github.com/gwkim92/stockA/pull/52. 최종 구현 c0e892a3, develop merge 57b6bba9bf0f66605220472f27d117e1134bd8b4.
- Web Product Quality 34513973462 성공. Evaluation History 34513973361 성공. Analysis Prompt Quality 34513973346의 Python 3.11/3.13 계약, 실제 PostgreSQL atomic/cutoff 성공.
- Web Runtime Artifact 34514010547 성공. commit c0e892a3f9ca28f14cb320dd7f8fac552551bcaf, BUILD_ID PGVFE-6JtVuU6b53yBvzj, SHA-256 f88c276adafca5392cb9e6810ea3959895172189dd6e531a5e92436ca4483a6c. EC2 준비 폴더에서 sha256sum 검사도 통과했다.
- 로컬 검토 노트 대표 3개와 전체 desktop/mobile 112개 통과. 로컬 WebKit 바이너리는 없어 그 56개는 실행하지 못했다. CI에는 WebKit이 설치되어 전체 검사를 통과했다.

## 이전 운영 활성화 보류 이력

개인 계정 115623963546 / i-029d51b163fb07b61 / us-east-1을 새 IMDS 조회로 확인했다. 운영 커밋은 여전히 359e8531, 세 서비스 active, API ready=ok, 웹 200이다. 산출물과 스크립트만 `/opt/stockanalysis/runtime/purpose-fit-recovery-20260911/`에 준비했다.

활성화 명령은 실행 전에 자동 승인 검토에서 거절되었다. 사유는 운영 EC2 서비스·타이머·빌드 교체와 데이터 복구에 대한 구체적인 사용자 승인이 부족하다는 것이었다. 명령은 실행되지 않았으며 activation receipt는 없다. 성과 backfill, calibration/router 저장, 기업 AI 호출은 수행하지 않았다. 별도 경로로 우회하지 않는다.

## 승인 후 운영 결과

- 사용자 “진행” 승인 후 activate_runtime.py 성공. develop 57b6bba9, BUILD_ID PGVFE-6JtVuU6b53yBvzj. 환경 hash/권한 및 모델 Terra revision 2 동일, 서비스 3개 active, 타이머 13개 복원, 주요 화면 200.
- 실행 직전 기준 행을 새로 보관했다. 기존 추천 성과 224개/thesis 성과 126개. 신규 추천 성과 1,009개를 237/322/340/110개 묶음으로 저장. parent run 23731/23752/23773/23794, 실패 0개.
- outcomes-verified.json: 추천 1,358, 점수 구성요소 32,593, 포지션 515, 벤치마크 612 및 기존 outcome 행 hash 보존. 추천 성과 1,233개, thesis 성과 746개.
- calibration 23801/eval 1756, router 23804/eval 1757. 지정 기간 감사 측정 1,128개, 미처리 0개, 가격 gap 0개, 미도래 4,304개. 다음 측정일 2026-09-11/21개. 자동 weight 변경과 주문은 false.
- 운영 NVDA/ARM 목록·상세 decision_boundary 동일. 과거 AAPL recommendation-477은 2026-07-24 성과와 outcome_measured=true를 반환했다.
- 운영 Chrome 기업/추천 상세/성과/data-health × desktop/mobile 8개 화면: 200, overflow false, pageerror 0. 원천 문서 40343 표시, 모바일 패널, Escape 닫기, 입력 문서 버튼으로 focus 복귀 확인.
- 모델 화면에는 Codex 사용처 5개와 기본 Terra, 실제 CLI 선택 모델, 관리자 변경 UI가 표시된다. 이번 세션은 조회 전용이며 설정 저장을 실행하지 않았다.

## 추가 승인 전 보류와 남은 한계

- 실제 기업 리서치 명령은 실행 전 자동 승인 검토에서 payload/외부 목적지별 승인 부족으로 거절됐다. 전송 자료 사전 검사 후 같은 명령을 재검토 요청했으나 재거절됐다. 호출·생성 결과는 없다. 현재 화면은 기존 fallback이다. 구체적인 전송·저장 승인 질문에 대한 답변을 기다린다.
- 전송 예정 3개 자료의 크기는 15,854/15,941/14,213자이며 계좌/보유 테이블을 포함하지 않는다. 인증값과 DB주소 패턴은 검출되지 않았다. 앱의 기존 추천/thesis는 포함한다. 검사 원본은 research-payload-preflight.json이다.
- 성과 메인 화면은 별도 attribution_run 기준이다. 2026-09-10 및 09-04는 귀속 보고서 없이 0행을 표시한다. 전체 추천 성과 복구와 포트폴리오 귀속 보고서 완료를 구분한다.
- data-health open gates 8개가 남는다. 상세 목록과 다음 작업은 handoff.md를 따른다.

운영 캡처와 기록은 output/playwright/purpose-fit-production-*.png, output/purpose-fit-recovery-20260911/에 보관했다. 소스·평가 기준을 추가 변경하지 않아 통과한 CI/전체 검사를 불필요하게 반복하지 않았다.

## 실제 기업 리서치 완료 — 2026-09-11 00:15~00:16 UTC

전송 자료·OpenAI Codex OAuth/Terra 목적지·운영 DB 저장을 명시한 재질문에 사용자가 “진행”으로 승인했다. 같은 research 명령이 승인돼 한 번 실행됐다. 이전 자동 승인 검토 보류는 해소됐다.

- NVDA: run 23818 / invocation 41113 / artifact 492. AAPL: 23819 / 41114 / 493. ARM: 23820 / 41115 / 494.
- 3건 모두 primary, 실제 모델 gpt-5.6-terra, 실패와 fallback 0건. receipt의 model_name과 운영 API의 artifact/model/generation이 일치한다.
- API 3건 및 NVDA 추천 상세 확인. source_document_count 6/4/2, structural_status complete, content_review_status not_recorded. 생성과 내용 검증을 구분한다.
- 모델 설정 revision 2, 기본 Terra와 overrides 없음 유지. 기업 리서치 최근 CLI 선택/actual_model Terra 성공 및 DB 호출 41115 확인.
- research-verified.json: 기존 보호 데이터 보존 통과, 추천 성과 1,233/thesis 성과 746 유지.
- Chrome 3개 기업 × desktop/mobile 6개 화면: 200, AI/모델 표시, overflow false, pageerror 0. 원천 12개 모두 200이며 발췌가 있다. ARM source-document-36751의 패널과 모바일/닫기 확인.
- AAPL 입력의 event-19/source-document-22에서 영문 제목·번역·AAPL 연결 불일치를 추가 발견했다. 이번 호출의 입력 계층 문제이며 해당 이벤트는 생성 본문의 핵심 주장이나 촉매로 인용되지 않았다. 삭제·재분류·추가 생성 없이 후속 과제로 기록했다.
- 상세 내용 검토 및 의미의 한계: research-review.md. 캡처: output/playwright/purpose-fit-ai-*.png. 검사 JSON과 원본은 output/purpose-fit-recovery-20260911/에 보관했다.

이번 단계는 준비된 운영 명령과 기존 빌드를 사용했으며 소스·스키마·평가 기준을 변경하지 않았다. 이전 통과 CI를 유지하고 실제 실행·API·화면에 맞는 검증을 추가했다.
