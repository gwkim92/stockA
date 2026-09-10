# 독립 구현·테스트 평가

평가일: 2026-09-10. 검토 HEAD: `80769207c4a3610b8e8c21320c43ad2791a720a9`.

읽기 전용으로 사용자 흐름의 데이터 연결과 상태 표현을 추적했다. 브라우저 관찰은 주 에이전트가 전달한 결과이며, 이 검토자는 브라우저·운영 서버를 조작하지 않았다. 아래 결함은 코드 근거를 확인했고 운영 재현 여부를 각각 분리했다. 앱 코드·모델·DB·배포 설정은 변경하지 않았다.

## 주요 판단

추천·기업·근거·검토·성과의 자료 구조와 방어 로직은 상당 부분 구현되어 있다. 그러나 목록이 커졌을 때의 탐색과 여러 화면 사이의 상태·기준일 연결에는 실제 기능 결손이 남아 있다. 특히 종목 탐색의 첫 페이지 제한은 데이터가 존재하는 기업도 사용자가 검색해서 찾지 못하게 한다. 화면 상단의 정상/기준일 문구 일부는 실제 조회한 원천을 정확히 반영하지 않는다.

## Findings

### IMP-01 / P1 — 종목 탐색은 API 첫 50개 이후를 검색하거나 열람할 수 없다

- 확정 코드: [discovery-data.ts](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/lib/discovery-data.ts:6)는 항상 `/api/stocks`를 한 번 요청한다. [pagination.py](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/pagination.py:10)의 기본 페이지 크기는 50이다.
- [discovery-model.ts](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/lib/discovery-model.ts:30)는 `has_more`를 `partial`로만 보존하고 다음 cursor를 버린다. [StockExplorer.tsx](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/components/discovery/StockExplorer.tsx:11)는 수신 배열 안에서만 필터링한다. [DiscoveryControls.tsx](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/components/discovery/DiscoveryControls.tsx:15)의 검색 변경은 브라우저 주소만 바꾼다. 서버 검색이나 다음 페이지 UI가 없다.
- 주 에이전트 운영 관찰: `/stocks`는 `일부 결과` 50개, A~LLY 범위만 표시한다. NVDA/MSFT 검색과 직접 상세 주소 비교는 주 에이전트 QA에서 확인한다.
- 재현: 종목이 50개를 초과하는 상태에서 `/stocks`를 열고 첫 페이지에 없는 종목을 검색한다. `조건에 맞는 결과가 없습니다`가 나오며 추가 페이지로 갈 수 없다. API pagination이 존재해도 화면에서 접근할 수 없다.
- 영향: 기업명/코드를 통한 주 리서치 진입 경로가 데이터 증가에 따라 잘린다. 추천/보유 필터도 첫 페이지 부분 집계에만 적용된다.
- 개선: cursor 기반 추가 페이지 또는 서버 검색을 연결하고, 검색 상태와 pagination을 주소에 보존한다. 첫 50개 이후 종목을 검색→상세 진입하는 통합 시나리오가 필요하다.

### IMP-02 / P2 — 홈의 보유 재검토 우선순위가 반복된 과거 티켓으로 채워진다

- 확정 코드: [live_adapter.py](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/live_adapter.py:5465)는 전체 open remediation 티켓을 읽는다. [동일 SQL](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/live_adapter.py:5512)은 종목·action별 최신화/그룹화 없이 전부 집계한다.
- 정렬에 쓰는 `review_date`와 `remediation_ticket_id`는 JSON 응답에서 빠진다. [홈](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/app/page.tsx:98)은 첫 5건을 그대로 각각의 검토 우선순위로 표시한다.
- 주 에이전트 운영 재현: `/`의 `보유 논리 재검토`에 TSLA, MSFT, TSLA, MSFT, TSLA가 보였고 모두 `과대 비중 축소 검토`였다. 첫 두 쌍은 비중 설명까지 같고 회차·기준일 구분이 없었다.
- 영향: 서로 다른 검토 대상 5개처럼 보이지만 같은 문제의 이력이 자리를 차지해 다른 종목이 밀려난다. 각 행이 현재 검토인지 과거 미종결인지 구별하기도 어렵다.
- 개선: 홈은 종목·문제별 현재 검토를 집계하고 반복 티켓 수/최근 기준일을 표시한다. 이력 전체는 상세 큐에서 유지한다. 현재 단위 fixture는 [test_frontend_live_adapter.py](/Users/woody/Documents/ChatGPT/stockA/tests/test_frontend_live_adapter.py:88)의 단일 BABA 사례라 중복 회차를 검증하지 못한다.

### IMP-03 / P2 — 조회하지 않은 AI 역할 실행 이력을 0건·오류 없음으로 표시한다

- 확정 코드: [live_adapter.py](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/live_adapter.py:547)는 모든 등록 역할의 `last_run_at`, `latest_model`, `latest_error_code`를 빈 문자열로 반환하고 `last_run_status=not_loaded_in_this_view`라고 명시한다. 실제 실행 DB를 조회한 결과가 아니다.
- [AI 페이지](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/app/admin/ai-agents/page.tsx:242)는 이 빈 값을 개수로 집계한다. [같은 화면](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/app/admin/ai-agents/page.tsx:394)은 `최근 실행 기록 0/13`, `최근 오류 0개`, `중대한 오류 없음`으로 렌더링한다.
- 주 에이전트 운영 재현: 상단 모델 설정에는 실제 작업 호출 이력이 있는데, 아래 역할 요약은 0/13으로 표시됐다.
- 영향: 미조회가 실행 없음/문제 없음으로 바뀐다. 사용자는 같은 화면에서 서로 다른 실행 상태를 읽게 된다. 실제 장애가 없다는 증거도 되지 않는다.
- 개선: 등록 정책 영역에서 실행·오류 집계를 제거하거나 `실행 이력 미연결`로 표시한다. 실제 이력을 보여주려면 역할의 `default_task_name`으로 실행 원천과 연결하고 조회 상태와 0건을 구분한다.

### IMP-04 / P2 — 뉴스 인텔리전스의 기준일과 근거 연결률이 포트폴리오 자료에서 온다

- 확정 코드: [intelligence/page.tsx](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/app/intelligence/page.tsx:353)의 `dashboard`는 `/api/dashboard/today` 포트폴리오 응답이다. [391행](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/app/intelligence/page.tsx:391)은 그 `as_of_date`를 `뉴스 인텔리전스` 기준일로 표시한다.
- 해당 API 기준일은 [live_adapter.py](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/live_adapter.py:5497)의 최신 포트폴리오 검토일 또는 보유 snapshot 날짜다. 뉴스 기준일이 아니다.
- 같은 화면의 [403행](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/app/intelligence/page.tsx:403)은 `weight_coverage_ratio`를 `추천 근거 연결률`로 부른다. 실제 분모/분자는 [5456행](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/live_adapter.py:5456)과 [5534행](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/live_adapter.py:5534)의 보유 비중 대비 thesis 연결 비중이다.
- 주 에이전트 운영 재현: 뉴스 헤더 2026-09-07과 하단 뉴스 09-09가 함께 표시됐다.
- 영향: 뉴스의 최신성을 포트폴리오 날짜로 판단하게 되고, 보유 비중의 연결 상태를 추천 근거의 품질/충족률로 해석할 수 있다.
- 개선: 뉴스/뉴스 묶음의 기준일을 각각 표시한다. 포트폴리오 지표를 유지한다면 `보유 비중 중 투자 논리 연결 비율`처럼 원천과 분모를 명시한다.

### IMP-05 / P2 — 성과 실행이 없을 때 커버리지 게이트를 통과로 표시한다

- 확정 코드: [live_adapter.py](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/live_adapter.py:11808)는 요청 종료일과 정확히 일치하는 `attribution_run`을 선택한다. [coverage_exclusions](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/live_adapter.py:11874)도 그 실행에 연결된 보유 snapshot에서 시작한다. 실행이 없으면 커버리지를 검증한 대상도, 제외 목록도 없다.
- 그러나 [12087행](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/live_adapter.py:12087)은 제외 행 수가 0이라는 이유만으로 `coverage_ready=passed`, `Portfolio positions have thesis/outcome coverage.`를 반환한다. [11969행](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/live_adapter.py:11969)의 제외 비중도 0으로 표현된다.
- 주 에이전트가 저장한 [performance-desktop.json](/Users/woody/Documents/ChatGPT/stockA/artifacts/product-evaluation-20260910/snapshots/performance-desktop.json)을 직접 읽어 확인했다. 2026-09-10 조회는 측정 구간 시작일 미확인, 측정 추천 0개, `no outcome data`인데 `커버리지 준비 / 통과`와 위 영문 사유를 함께 표시한다.
- 2026-09-07 보유 화면의 성과 기록 누락과 09-10 성과 화면을 같은 기준일이라고 비교하지 않았다. 이 문제는 실행이 없는 요청일 자체를 통과로 처리하는 조건 오류다.
- 영향: 사용자가 미측정을 커버리지 준비 완료·제외 비중 0%로 읽을 수 있다. 다른 `outcome_run` 게이트는 차단되므로 전체 성과 준비나 주문 허용으로 확대 해석하지 않는다.
- 개선: 실행과 검증 대상이 없으면 `not_evaluated` 또는 `unavailable`로 반환하고 제외 비중은 미확인으로 표시한다. 실행 없음·실행 있음/대상 없음·검증 대상 모두 충족을 구분해 검사한다.

### IMP-06 / P2 — 뉴스 목록의 원천 링크가 찾을 수 없는 화면으로 이어진다

- 추가 요청에 따라 원천 문서 한 건만 좁혀 확인했다. [intelligence-desktop.json](/Users/woody/Documents/ChatGPT/stockA/artifacts/product-evaluation-20260910/snapshots/intelligence-desktop.json)의 `원문`과 [evidence-desktop.json](/Users/woody/Documents/ChatGPT/stockA/artifacts/product-evaluation-20260910/snapshots/evidence-desktop.json)의 `원천 문서`는 모두 `/source-documents/source-document-rss%3Ayahoo-finance-news%3Abc514fa20dd706c5cdd354a6`로 연결된다. [detail-source-desktop.json](/Users/woody/Documents/ChatGPT/stockA/artifacts/product-evaluation-20260910/snapshots/detail-source-desktop.json)에 해당 경로의 `찾는 화면이 없습니다`가 저장돼 있다. 주 에이전트가 실제 목록 링크 클릭과 목적지 도착도 확인했으며 [issue-006-list-after.json](/Users/woody/Documents/ChatGPT/stockA/artifacts/product-evaluation-20260910/snapshots/issue-006-list-after.json), [재현 영상](/Users/woody/Documents/ChatGPT/stockA/artifacts/product-evaluation-20260910/videos/issue-006-source-link-confirmed.webm)에 증거가 있다.
- 같은 뉴스의 [ai-evidence-3665 상세 snapshot](/Users/woody/Documents/ChatGPT/stockA/artifacts/product-evaluation-20260910/snapshots/detail-evidence-item-desktop.json)은 접두사 없는 `/source-documents/rss%3Ayahoo-finance-news%3Abc514fa20dd706c5cdd354a6`를 제공한다. 이후 주 에이전트가 그 링크도 실제 클릭했고, [issue-006-source-canonical.json](/Users/woody/Documents/ChatGPT/stockA/artifacts/product-evaluation-20260910/snapshots/issue-006-source-canonical.json)에서 똑같이 `찾는 화면이 없습니다`를 확인했다. **접두사 있는 URL만 실패한다는 가설은 폐기했다.**
- 목록 origin 확정: `/intelligence`는 [getEvents 결과](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/app/intelligence/page.tsx:356) 중 AI 후보의 [source_document_id](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/app/intelligence/page.tsx:661)를 사용한다. `/ai-evidence`도 [getEvents 후보 조회](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/app/ai-evidence/page.tsx:172) 후 [CandidateCard](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/app/ai-evidence/page.tsx:101)에서 같은 필드로 링크를 만든다.
- ID 차이의 코드 원인 확정: 이벤트 목록 [live_adapter.py:19674](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/live_adapter.py:19674)는 비숫자 RSS external ID에도 `_opaque_id('source-document', ...)`를 적용해 접두사를 붙인다. AI 상세는 [3602행](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/live_adapter.py:3602)의 전용 함수가 [22080행](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/live_adapter.py:22080)에서 비숫자 ID를 그대로 유지한다. 실제 두 함수를 외부 IO 없이 실행해 위 두 문자열이 생성되는 것을 확인했다.
- **404의 직접 원인은 아직 미확정이다.** 현재 소스의 [SQL resolver](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/live_adapter.py:14427)는 접두사를 제거한 external ID 조회를 지원하고, [프런트 identity 검사](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/lib/research-reader-model.ts:61)도 prefix alias를 허용한다. ID 생성 차이는 관찰 사실이며 404 원인으로 채택하지 않는다.
- 범위를 더 좁힌 코드 사실: [원천 페이지](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/app/source-documents/[documentId]/page.tsx:10)는 `identifier` 또는 `not-found`일 때만 `notFound()`를 호출한다. [로더](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/lib/research-reader-data.ts:23)는 backend 404를 `not-found`로 바꾸며 응답 identity/title 파싱 실패는 `invalid`로 별도 처리한다. [현재 backend](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/live_adapter.py:3829)는 해당 문서 SQL 결과를 DTO로 조립하며 문서 없음 자체를 404로 만드는 분기가 없다. 문서가 없으면 SQL [14486행](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/live_adapter.py:14486)의 ID/title이 null이 되고, 현재 프런트 파싱 경로상 `invalid` 안내가 예상된다. 따라서 이번 404만으로 원천 자료가 DB에서 삭제됐다고 판단할 수 없다. 인코딩된 params/실제 backend 요청 경로·HTTP 상태/운영 로드 코드 대조가 남아 있다.
- 영향: 사용자가 모델 요약에서 원천 근거를 대조하는 핵심 클릭 흐름이 끊긴다. 수집 누락이나 원문 자체 부재라는 결론으로 확대하지 않는다.
- 개선: 먼저 실제 클릭에서 발생한 backend 응답을 확인하고, 이벤트/AI 상세의 문서 ID 생성 규칙을 일관되게 사용한다. RSS external ID의 prefix 유무와 URL 인코딩을 포함하는 목록→원천 통합 검증이 필요하다.
- 검사 범위: 기존 [reader E2E](/Users/woody/Documents/ChatGPT/stockA/apps/web/tests/e2e/research-readers.home.ts:21)는 `source-document-1` 숫자형 경로로만 전체 클릭 연결을 확인한다. [live adapter 원천 테스트](/Users/woody/Documents/ChatGPT/stockA/tests/test_frontend_live_adapter.py:8565)는 하이픈형 AAPL external ID를 fake executor로 검증한다. 이번처럼 콜론이 URL 인코딩된 RSS ID의 Next→FastAPI 전체 연결을 이 두 검사는 보장하지 않는다. 추가 확인에서는 코드/기존 테스트만 읽었으며 운영 endpoint나 DB를 조회하지 않았다.

### IMP-07 / P1 — 오래된 계산 지표를 최신 재무 모델과 새 추정 입력에 사용할 수 있다

- 주 에이전트가 저장한 [NVDA 전문 분석 snapshot](/Users/woody/Documents/ChatGPT/stockA/artifacts/product-evaluation-20260910/snapshots/detail-financial-desktop.json)을 직접 확인했다. `최근 연간 재무 모델`, 최근 기간 `2026-02-20`, 계산 완료 `12/14`인데 잉여현금흐름률 19.3%, CAPEX 부담 3.5%, FCF/순이익 132.6%의 기간은 모두 `2012-01-29`다. 다른 지표는 2026년 1~2월이다. 같은 화면의 `2026-09-07` 재무 추정 입력에는 기준 시나리오 FCF 마진 19.3%가 표시되고 상단은 `투자 판단 입력 가능`, `부족한 근거 없음`, `추가 보강 필요 없음`이다.
- **최신 모델의 기간 혼합 원인은 코드로 확정했다.** [live_adapter.py:8931](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/live_adapter.py:8931)은 지표별 한 행을 고를 때 기간 내림차순보다 `metric_status = computed`를 먼저 정렬한다. 최신 기간에 계산 불가 행이 있어도 오래된 계산 완료 행이 선택된다. 허용 연령이나 지표 사이의 동일 기간 조건이 없다. [9364행](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/live_adapter.py:9364)은 전체 기간의 최댓값을 모델의 최근 기간으로 표시하고, [9370행](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/live_adapter.py:9370)은 선택된 오래된 행도 계산 완료 수에 포함한다. [14757행](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/live_adapter.py:14757)은 완료 지표 6개 이상이면 `available`로 만들며 [14768행](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/live_adapter.py:14768)의 요약은 이를 `최근 연간 재무 모델`이라고 부른다.
- **화면 표시를 넘어 실제 추정 생성 경로에도 같은 시점 검증 누락이 있다.** [professional_equity_analysis.py:1231](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/operations/professional_equity_analysis.py:1231)의 forecast upsert SQL은 지표별 `computed` 이력에서 행을 고른다. 조회 기준일 이하라는 조건은 있지만, 원천 `period_end`의 허용 연령이나 최신 매출과의 기간 일치 조건이 없다. [1285행](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/operations/professional_equity_analysis.py:1285)은 선택된 정규화 FCF 마진을 raw 현금흐름 재계산보다 우선하며, [1300행](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/operations/professional_equity_analysis.py:1300)의 CAPEX 비율도 같은 구조다. 2012년 값이어도 계산 완료이고 선택 조건을 만족하면 사용된다.
- 이 값은 [1368행](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/operations/professional_equity_analysis.py:1368)에서 미래 매출 × FCF 마진으로 실제 추정 현금흐름을 계산하고, [1391행](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/operations/professional_equity_analysis.py:1391)의 `market.financial_forecast_input`에 새 기준일로 저장된다. 실행 runner가 이 SQL을 호출하는 경로는 [1530행](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/operations/professional_equity_analysis.py:1530)에 있다. SOTP도 [2631행](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/operations/professional_equity_analysis.py:2631)에서 저장된 forecast를 읽고 [3109행](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/operations/professional_equity_analysis.py:3109)에서 영업사업 가치의 FCF로 우선 사용한다. 따라서 오래된 지표가 추정·가치평가 입력으로 전달될 수 있는 기능 결함이며, 날짜 라벨만 고쳐서 해결할 수 없다.
- 추정 근거도 [1262행](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/operations/professional_equity_analysis.py:1262)의 `max(period_end)` 하나로 합쳐지고 [1375행](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/operations/professional_equity_analysis.py:1375)에 저장된다. 개별 FCF/CAPEX 지표의 원천 기간은 이 assumptions에 남지 않는다. 신뢰도는 [1387행](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/operations/professional_equity_analysis.py:1387)의 지표 개수 기반이며 시점 차이를 반영하지 않는다.
- 상단 사용 가능 판단은 [live_adapter.py:14887](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/live_adapter.py:14887)의 지정 원천 차단 코드 여부로 정해진다. 차단 코드가 없으면 [14929행](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/live_adapter.py:14929)은 `clear`와 전문 판단/페이퍼 검증 입력 가능을 반환하며 위 지표 연령을 검사하지 않는다. 다만 주문 전송과 자동 주문은 이 경로에서도 계속 차단되므로 실거래 허용 문제로 확대하지 않는다.
- **확정과 미확정:** 운영 화면의 2012/2026 기간 혼합과 같은 19.3% 표시는 확정이다. 오래된 계산값이 실제 forecast 생성에 선택될 수 있는 코드 경로도 확정이다. 해당 NVDA의 2012 원천 행이 09-07 forecast의 직접 부모였는지는 운영 DB의 행 ID·source run을 읽지 않아 미확정이다. UI 선택과 forecast 선택의 정렬 순서도 완전히 같지는 않으므로 값 일치만으로 그 계보를 단정하지 않는다. 외부 공시 수치 자체와 목표가 정확성은 조사하지 않았다.
- 재현 조건: 최신 연간 FCF/CAPEX가 계산 불가이고 과거 연도에 계산 완료 값이 있는 기업을 조회하면 과거 행이 `최근` 모델의 완료 수에 포함된다. 같은 데이터를 추정 SQL에 넣으면 유효 기간 제한 없이 그 계산값이 현재 매출과 결합될 수 있다. [기존 forecast SQL 테스트](/Users/woody/Documents/ChatGPT/stockA/tests/test_professional_equity_analysis.py:537)는 SQL 구조와 추천 점수 비변경을 검사하지만 이 오래된 값/최신 결측 조합의 선택 결과는 검증하지 않는다. 이번 추가 검토에서는 SQL이나 운영 작업을 실행하지 않았다.
- 개선 우선순위: 먼저 운영 NVDA 추정의 원천 행 계보를 확인한다. 최신 연간 모델은 기준 기간을 맞추고 과거 보충 값은 별도로 표시한다. 추정 입력에는 지표별 원천 기간·행 ID를 보존하고 허용 연령/기간 일치가 충족되지 않으면 현재 입력으로 자동 승격하지 않도록 해야 한다. 사용 가능 상태와 계산 완료 비율에도 이 결측을 반영하고, 오래된 계산값 + 최신 결측 사례로 조회·추정 생성·사용 가능 상태를 함께 검증한다.

## 추가 조사 대상 — 확정 결함과 분리

- 데이터 상태 제목의 조건부 오류도 로컬 함수에서 재현했다. [presentation/operations.ts](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/lib/presentation/operations.ts:18)는 실패 실행과 AI attention만 정상/점검 판정에 사용한다. 실제 source를 메모리에서 실행해 `overall_status=attention_required`, 실패 0, stale 자료 1개, AI ready를 넣으면 `운영 정상 / ready`와 `최신성 이슈 1건`이 함께 반환된다. 운영에서 현재 이 조합인지는 미확인이다. API 전체 상태·최신성·미확인을 제목에 반영하는 후속 검토가 필요하다.
- `/intelligence`는 [page.tsx:353](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/app/intelligence/page.tsx:353)의 4개 응답을 `Promise.all`로 모두 기다린다. 공통 [fetchFrontendPayload](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/lib/frontend-api.ts:51)는 호출자가 signal을 주지 않으면 프런트 응답 기한이 없고, 해당 4개 호출자는 이를 주지 않는다. 주 에이전트 첫 탐색 약 21.5초와 구조적으로 연관될 수 있지만, 어느 API가 병목인지는 계측하지 않았다. FastAPI에는 기본 30초 middleware deadline이 있으므로 무한 대기를 단정하지 않는다. API별 지연과 부분 장애 격리 가능성을 확인할 필요가 있다.
- 개인 검토 노트는 브라우저 저장이라는 범위를 명확히 설명한다. 서버/다른 기기 동기화·이전 버전 누적·파일 가져오기·자동 알림이 없는 것은 현재 제품 범위의 제약이며 버그로 분류하지 않았다.

## 긍정적인 구현

- 홈의 각 데이터 영역은 5초 body deadline과 독립 실패 표시가 있다. 응답 생성 시각과 자료 기준일을 분리하고 과거/미확인을 현재로 바꾸지 않는다. [research-home-data.ts](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/lib/research-home-data.ts:17), [research-home-model.ts](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/lib/research-home-model.ts:68).
- 평가 이력은 평가 당시 snapshot을 저장하고 hash와 복사 필드를 대조한다. 현재 조회 실패가 과거 기록을 지우지 않으며, 후속 성과가 두 시점 사이의 추가 수익이 아님을 명시한다. [recommendation_eval_comparison.py](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/frontend/recommendation_eval_comparison.py:30), [EvaluationHistory.tsx](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/components/review/EvaluationHistory.tsx:40).
- 검토 노트는 종목과 기업 ID를 함께 확인하고, 다른 탭 변경·손상·저장소 실패를 빈 메모로 덮어쓰지 않는다. 분석 묶음이 바뀌면 예전 확인 체크를 새 자료에 자동 적용하지 않는다. [ReviewDraft.tsx](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/components/review/ReviewDraft.tsx:58), [review-continuity-model.ts](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/lib/review-continuity-model.ts:40).
- 실제 AI 설정은 5개 작업의 설정 모델, CLI 선택 모델, 운영 DB 기록을 구분하고 변경 후 실제 호출 확인 대기를 표현한다. 읽기 권한과 모델 변경 세션, revision 충돌, 변경 audit가 분리되어 있다. [model_settings.py](/Users/woody/Documents/ChatGPT/stockA/src/stockanalysis/ai/model_settings.py:162), [ModelSettingsPanel.tsx](/Users/woody/Documents/ChatGPT/stockA/apps/web/src/app/admin/ai-agents/ModelSettingsPanel.tsx:102).
- Web Product Quality CI에는 의존성 감사, Python 계약, frontend unit, production build, 타입 검사와 노트·평가·보유·원천·기업·뉴스의 브라우저 흐름이 포함돼 있다. [web-product-quality.yml](/Users/woody/Documents/ChatGPT/stockA/.github/workflows/web-product-quality.yml:107). 이번 결함은 이 검사가 없어서라기보다 페이지 크기·반복 운영 이력·서로 다른 날짜 원천을 포함하는 현실적인 데이터 조합이 부족한 영역이다.

## 실행한 검증

- 8개 frontend test file, 187 tests 통과: research-home, evaluation-history, review-continuity, review-inbox, company-review, review-workspace, ModelSettingsPanel, presentation/status.
- 프로젝트 `.venv` Python 3.13으로 evaluation_history_completion, ai_model_settings, research_display_contract 25 tests 통과. 기본 Homebrew Python 3.14 첫 시도에서는 FastAPI 미설치로 2개 import 오류가 났고, 기존 프로젝트 환경으로 재실행해 통과했다. 앱 결함으로 분류하지 않았다.
- `buildOperationsViewModel` 조건 재현은 source를 읽어 메모리에서 실행했으며 파일·운영 데이터는 바꾸지 않았다.
- 전체 테스트/전체 API/전체 투자 로직은 실행하지 않았다. 현재 GitHub CI 결과, 투자 성과의 정확성, 주문 실행, 외부 원천 정확성 또는 모든 기업의 재무 값은 이 독립 검토로 검증하지 않았다. 실제 브라우저 결과는 종합 QA 보고서와 교차 확인한다.
