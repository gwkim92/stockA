# professional-investment-workspace-redesign-v3 Handoff

## Status

- current status: implementation, Git integration, and EC2 deployment complete.
- 완료: 디자인 시스템, 투자자용 내비게이션, 운영 콘솔 분리, presentation 계층, 핵심 화면 정보 위계, 반응형·접근성 회귀 검사를 구현했다.
- 진행 중: 없음. 후속 대형 페이지 분해와 server action 사용자 인증은 별도 task가 필요하다.

## Completed

- `DESIGN.md`와 전체 route 제품 지도를 추가했다.
- 투자자용 presentation 계층과 공통 shell, status, summary, metric, list 컴포넌트를 추가했다.
- 1차 메뉴를 `오늘`, `시장`, `리서치`, `종목`, `추천`, `포트폴리오`로 고정했다.
- 홈, 종목 목록, 추천 목록, 뉴스 인텔리전스, 사이클 지도, 포트폴리오, 성과, 가상 매매 문구와 정보 위계를 개편했다.
- 종목·추천·AI 근거·포트폴리오 상세의 페이지 내부 문자열 변환을 공통 presentation 계층으로 이동했다.
- 데이터 상태, AI 운영, 거래 안전, 보완 작업에 공통 운영 콘솔 헤더를 적용했다.
- Vitest와 Playwright/axe 기반 회귀 검사를 추가했다.
- 추천 점수, schema, benchmark, portfolio position, AI 분석 로직, broker/order flow는 변경하지 않았다.

## Verification Evidence

- `npm test`: 14 tests passed.
- `npm run typecheck`: passed.
- `npm run build`: passed on Next.js `16.2.9`.
- Playwright final expanded run: 51/51 passed across desktop, tablet, mobile, detail routes, operations separation, navigation, and axe checks.
- Browser viewport checks: 375px, 768px, and 1280px all rendered without horizontal overflow. The mobile operations hero selector collision and Korean orphan-syllable table hint were corrected.
- Final live-data mobile check: `/data-health` rendered with `width=375`, `scrollWidth=375`, no raw internal codes, no error surface, and the shortened hint `상세 표는 좌우로 이동할 수 있습니다.`.
- Git: feature commit `38011cde`를 `develop`에 fast-forward하고 GitHub에 push했다.
- EC2: `/opt/stockanalysis/app`에서 `develop` commit `38011cde`를 pull하고 `npm ci`, `npm run typecheck`, `npm run build`를 통과한 뒤 `stockanalysis-web.service`를 재시작했다.
- EC2 route smoke: FastAPI `/__ready`와 `/`, `/market-map`, `/cycle-map`, `/intelligence`, `/stocks`, `/recommendations`, `/portfolio/coverage`, `/paper-trading`, `/data-health`, `/admin/ai-agents`, `/trading-readiness`, `/remediation`가 모두 `200`이다.
- EC2 copy smoke: 홈과 AI 운영 화면에서 `portfolio review action`, `coverage status`, `equity_research`, `missing_api_key`, `admin_key_missing`이 노출되지 않는다.
- EC2 services: `stockanalysis-frontend-api.service`, `stockanalysis-web.service` 모두 `active`.
- `verify_frontend_api_contract.sh`: passed.
- `verify_project_execution_roadmap.sh`: passed.
- AWH task readiness: passed.
- `git diff --check`: passed.
- Python frontend fixture tests passed, but the selected local runtime venv does not include FastAPI, so `test_frontend_api_server` could not import its dependency. The repository-wide Python suite also retains unrelated cadence-environment failures documented in the session.

## Remaining Risk

- `data-health`, 종목 상세, 추천 상세는 기능 범위가 커서 여전히 큰 페이지 파일이다. 이번 작업은 presentation 변환과 공통 UI 경계를 분리했지만, 추가 도메인 컴포넌트 추출은 후속 유지보수 작업으로 남는다.
- 실제 EC2 데이터에서는 fixture와 다른 긴 문구·빈 상태가 있을 수 있어 배포 후 route smoke가 필요하다.
- React Doctor는 기존 `admin/ai-agents` 서버 액션 4개에 사용자 인증 검사 부재를 보고했다. 해당 액션의 backend admin token 경계는 이번 UI 작업의 mutable surface 밖이므로 별도 security task에서 검토해야 한다.
- Next.js는 공개 high 보안 권고를 피하기 위해 동일 minor 패치인 `16.2.9`로 고정했다. Next 내부 `postcss`의 moderate 경고 2건은 framework support 경계를 벗어나는 강제 override 없이 남겼다.

## Next Step

- exact next step: `frontend-domain-component-extraction-v1`에서 `data-health`, 종목 상세, 추천 상세, AI 근거 상세를 도메인 컴포넌트로 분해한다.
- 다음 세션은 이것부터 시작: 대형 페이지 분해 전에 현재 51개 E2E와 API contract를 기준선으로 고정하고 `data-health`부터 읽기 전용 섹션 컴포넌트를 추출한다.
