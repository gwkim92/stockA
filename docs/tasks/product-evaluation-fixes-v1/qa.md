# 결함 수정 검증

## 범위와 상태

2026-09-10 평가의 ISSUE-001~010의 코드 수정을 완료했다. 현재 증거는 로컬 코드/빌드와 운영 데이터의 읽기 전용 조회다. 이 문서 작성 시점에 변경 코드를 운영 서비스에 적용하지 않았다. 기존 모델 Terra/revision 2, 인증 설정, 추천 weight, benchmark, 평가 데이터 분할, 주문 실행은 바꾸지 않았다.

## 수정과 회귀

| 평가 항목 | 수정 | 검증 |
|---|---|---|
| 001 홈 검토 반복 | 종목·action·문제별 최신 티켓, 최근일/미종결 이력 수 보존 | 실제 SQL 중복 2건→1행, 운영 읽기 TSLA/MSFT/AAPL 3개 |
| 002 첫 50개 검색 한계 | DB 검색 후 pagination, URL 검색/필터/cursor, 미수집 가격 종목 포함 | 61개 SQL 및 61개 브라우저 fixture에서 NVDA 검색·다음 페이지·새로고침, unpriced 별도 검증 |
| 003 AI 미조회→0건 | 정책 영역은 실행 이력 미조회, 오류 미조회; 실제 모델 패널 유지 | 타입/빌드, 운영 DTO를 사용하는 로컬 화면 검증 |
| 004 뉴스 기준일/지표 | 뉴스 조회 기준과 묶음 기준 표시, 포트폴리오 비율은 보유 비중 기준으로 명명 | 운영 읽기와 화면 대조 |
| 005 실행 없는 성과 통과 | 실행/대상 없으면 미평가, 모르는 제외 비중은 null; 평가 이력/수집 상태 링크 | no run / empty holdings / missing coverage / unknown weight 실제 SQL |
| 006 RSS 원천 404 | Next 인코딩된 segment를 1회 decode 후 기존 identifier 검증 | 숫자·콜론·접두사 두 경로, encoded delimiter 거부 단위 검증, reader E2E 38개 |
| 007 모바일 표 넘침 | 표 컨테이너 내부 가로 스크롤, 셀 줄바꿈 | 390px 가로 overflow 없음, 표 내부 스크롤 캡처 |
| 008 큰 도입/긴 목록 | 간결한 제목, 펼침 안내, 근거 10개·묶음 3개·분류 20개/페이지, cursor 연결 | 원문/기존 카드 유지, 12개 영향 화면 desktop/mobile 24개 모두 HTTP 200·문서 overflow 없음 |
| 009 과장/번역 | 뉴스 묶음·관측 점수로 명명, 측정 성과 없음/한도 내/종목 선택 | unit/type/build, 실제 문구 대조 |
| 010 재무 기간 혼합 | 연간 revenue 기간으로 원천/정규화 입력 일치, 최신 unavailable 보존, 새 forecast 지표별 lineage/default 기록, legacy forecast·FCF SOTP 소비 차단, 기존 valuation 계보 미검증 표시 | 실제 PostgreSQL 생성→SOTP→valuation 체인, 후행 shares-only 기간, 최신 전부 결측 입력 차단 |

## 현재 검증 결과

- Python 연관 검사: 195개 통과, `backend-tests.log` (임시 Postgres 실제 SQL 포함).
- 웹 단위 검사: 42개 파일, 523개 통과 (`web-unit.log`).
- 웹 타입 검사 및 production build 통과 (`web-build.log`).
- 종목 탐색 E2E: desktop/mobile 22개 통과 (`discovery-e2e.log`).
- 원천/논리 읽기 E2E: desktop/mobile 38개 통과. 숫자·RSS ID, 실제 클릭 연결, 접근성 포함.
- 임시 DB: PostgreSQL 16, 127.0.0.1:15439, 저장소 전체 migration 적용. 각 시나리오는 rollback하며 운영 DB와 연결되지 않는다. `STOCKA_TEST_PG_PORT`를 명시할 때만 SQL 테스트를 실행한다.
- 독립 구현 검토 최종 PASS: 기존 forecast 외에 legacy SOTP, DCF 직접 입력, revenue anchor, 결측 전문 입력 차단, unpriced 집계, null 비중 지적을 반영했다.

## 운영 데이터 읽기 증거

`artifacts/product-evaluation-fixes-v1/`에 JSON·로그·화면을 보존한다. 공개 배포/실제 AI 호출 증거가 아니다.

- `financial-live-before.json`: NVDA 2026-09-07 forecast_input_id 12876, source_run_id 22948, FCF margin 0.192705 / CAPEX intensity 0.034702. 지표별 기간·행 계보가 없어 특정 2012 행이 직접 부모였다는 주장은 하지 않는다.
- `financial-current-code-live-read.json`: 최신 매출 기간 2026-01-25, computed 9 / data gap 5. FCF/CAPEX/FCF-to-income 결측 유지. DCF/scenario/SOTP 기존 평가의 입력 기간은 미검증으로 표시한다.
- `home-current-code-live-read.json`: TSLA/MSFT 최근 2026-09-07, 미종결 이력 각각 79건. AAPL 최근 2026-07-29, 2건. 원래 티켓은 삭제하지 않는다.
- `stocks-search-current-code-live-read.json`: 등록 active 종목 8,038개, NVDA 검색 결과 1개. 종가 미수집 종목도 검색 대상으로 포함된다.
- `performance-current-code-live-read.json`: 2026-09-10 종료일의 실행 없음 → coverage_ready=not_evaluated, excluded_weight=null.

## 검증 도중의 오류와 구분

- browser fixture의 URL 변수명 및 바뀐 링크/빈 상태 명칭을 수정한 뒤 E2E를 재실행했다. 최종 22개 통과.
- 임시 SSH SQL executor의 line-based scalar 출력이 JSON row 배열 중간을 잘라 운영 조회 JSON을 한 줄 jsonb로 변경했다. 앱 SQL 실행 방식 변경은 아니다.
- data-health는 많은 작은 DB 읽기와 runtime 환경을 요구한다. SSH-per-query 로컬 미리보기에서는 실패하므로 해당 DTO 및 AI 운영 설정 DTO는 기존 운영 API에서 GET으로 읽는다. 수정 SQL 검증과 운영 runtime 상태를 혼동하지 않는다. 로컬 미리보기 전체는 GET/HEAD/OPTIONS만 허용한다.

## 최종 화면/상호작용 확인

- 영향 12개 경로 × desktop 1440px/mobile 390px에서 HTTP 200, 문서 가로 넘침 없음. 마지막 문구/단계 이동 수정 후 6개 화면 × 2를 다시 캡처했다.
- 실제 뉴스 근거 첫 10개→다음 10개가 중복 없이 이동하고, 새로고침 및 첫 페이지 복귀가 같은 목록을 보존한다. 목록의 인코딩된 RSS 원천 링크를 클릭해 문서가 열렸다. 두 viewport에서 확인했다.
- 모바일 AI 표는 문서 너비 390px 안의 356px 컨테이너에서 560px 내용을 스크롤한다. 키보드 ArrowRight로 scrollLeft 0→204를 확인했다.
- 통과 근거 모바일 길이는 기존 약 69,000px에서 11,803px로 줄었다. 원문 근거 카드는 보존하고 페이지당 10개와 접힌 안내를 사용한다.
- 최종 화면 데이터: `final-interactions.json`, `preview-ui.json`; 제목 잘림 의심은 hero 확대 캡처와 좌표(`hero-bounds.json`, 내부 padding 24px)에서 재현되지 않았고 독립 검토자가 판독 오류로 철회했다. 최종 화면 검토 PASS.

## 남은 범위

Linux runtime artifact 및 운영 반영 결과는 후속 기록한다. 과거 저장 valuation/forecast를 수동 재생성하거나 소급 수정하지 않는다. 새 계산은 기존 시나리오 수치/가정을 유지하지만 같은 재무 기간의 입력만 사용하므로 계산 값과 입력 가능 상태가 달라질 수 있다. 이것은 입력 정합성 수정이며 투자 성능 개선의 증거가 아니다.
