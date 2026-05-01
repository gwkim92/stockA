# Task Contract

## Task

- 이름: frontend-browser-visual-qa
- 요청: expanded frontend를 실제 브라우저로 검증하고 발견된 시각/UX 문제를 수정한다.
- 담당: Codex
- 날짜: 2026-05-01

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: fixture-backed `apps/web` 주요 route가 실제 브라우저에서 로드되고, 새로 추가한 event/theme/performance 화면의 치명적 layout, navigation, console 문제가 없거나 수정되어 있다.

## Scope

- 포함:
  - fixture server와 Next app을 로컬로 실행
  - 브라우저로 `/`, `/events`, `/themes/ANNUAL_REPORTING`, `/performance`, `/portfolio/coverage`를 검토
  - viewport desktop/mobile 기본 검토
  - console/runtime error 확인
  - 발견한 UI/UX 문제 중 작고 안전한 수정 반영
  - QA report와 task handoff/review 갱신
- 제외:
  - live DB read adapter
  - auth/RBAC
  - performance/outcome/benchmark 산식 변경
  - 투자 추천 로직 변경
  - 배포 설정 변경

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/`
  - `apps/web/src/lib/`
  - `docs/apps-web-scaffold.md`
  - `docs/frontend-architecture.md`
  - `docs/verification-plan.md`
  - `docs/tasks/frontend-browser-visual-qa/`
- 수정 금지 파일:
  - DB migrations
  - scoring/evaluation benchmark
  - secrets
  - live trading integrations
  - performance/outcome calculation modules

- 검증에 사용할 명령:
  - `bash scripts/verify_frontend_detail_routes.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-browser-visual-qa`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Completion Criteria

- [x] Browser QA report exists with scope, route coverage, findings, and evidence paths.
- [x] Desktop browser smoke covers the expanded frontend routes.
- [x] Mobile or narrow viewport smoke covers navigation/readability.
- [x] Console/runtime errors are checked.
- [x] Any accepted small UI fixes are implemented and verified.
- [x] AWH readiness checks pass.

## Risks

- QA uses fixture data, not live market data.
- Browser QA may identify issues that are too broad for this task; those should be recorded rather than silently expanded.
