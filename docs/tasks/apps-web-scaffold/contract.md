# Task Contract

## Task

- 이름: apps-web-scaffold
- 요청: fixture server를 데이터 소스로 사용하는 첫 `apps/web` frontend scaffold를 만든다.
- 담당: Codex
- 날짜: 2026-05-01

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `apps/web` Next.js App Router 앱이 존재하고, fixture server에서 dashboard/remediation/data-health/cycles DTO를 읽는 read-only investment cockpit shell이 검증된다.

## Why

- 지금까지는 데이터 파이프라인, contract, fixture adapter/server까지 준비됐지만 사용자가 볼 수 있는 frontend가 없었다.
- 브라우저 smoke와 UX 검토를 시작하려면 최소 UI shell이 필요하다.

## Scope

- 포함:
  - `apps/web` Next.js App Router scaffold
  - RSC 기반 fixture API fetch client
  - `/`, `/remediation`, `/data-health`, `/cycles` initial route shell
  - repo-local visual system
  - web scaffold verification script
  - 기존 frontend verification script의 obsolete absence gate 갱신
  - docs/task handoff 갱신
- 제외:
  - live DB read adapter
  - write endpoint
  - remediation ticket mutation
  - auth/RBAC
  - broker integration
  - production deployment

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/plans/2026-05-01-apps-web-scaffold.md`
  - `docs/apps-web-scaffold.md`
  - `docs/frontend-architecture.md`
  - `docs/frontend-fixture-server.md`
  - `docs/tasks/apps-web-scaffold/`
  - `docs/verification-plan.md`
  - `scripts/verify_apps_web_scaffold.sh`
  - `scripts/verify_frontend_architecture.sh`
  - `scripts/verify_frontend_api_contract.sh`
  - `scripts/verify_frontend_api_adapter.sh`
  - `scripts/verify_frontend_fixture_server.sh`
  - `apps/web/`
  - `.gitignore`
- 수정 금지 파일:
  - DB migrations
  - deployment secrets
  - scheduler activation artifacts
  - live trading integrations
- 검증에 사용할 명령:
  - `bash -n scripts/verify_apps_web_scaffold.sh`
  - `bash scripts/verify_apps_web_scaffold.sh`
  - `bash scripts/verify_frontend_fixture_server.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task apps-web-scaffold`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - `apps/web` Next.js app
  - route shell and data client
  - web verification script
  - docs
  - task contract/plan/handoff/review

## Completion Criteria

- [x] `apps/web/package.json`과 Next App Router files가 존재한다.
- [x] `/`, `/remediation`, `/data-health`, `/cycles` route가 fixture payload를 읽는다.
- [x] browser-side DB/API secret이 없다.
- [x] write endpoint가 없다.
- [x] 기존 frontend verification scripts가 `apps/web` 존재 때문에 실패하지 않는다.
- [x] web scaffold verification이 통과한다.
- [x] 하네스 검증이 통과한다.

## Risks

- fixture server가 실행되지 않으면 runtime page fetch가 실패한다.
- 첫 UI는 fixture-only라 live data freshness를 증명하지 않는다.
- package install/build는 Node/npm 환경에 의존한다.
