# Task Contract

## Task

- 이름: frontend-api-runtime-source-mode
- 요청: local frontend API runtime에서 fixture/live/auto source mode를 선택할 수 있게 한다.
- 담당: Codex
- 날짜: 2026-05-01

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `apps/web`이 바라보는 local read-only HTTP runtime을 `--source fixture|live|auto`로 시작할 수 있고, 기본 fixture 동작은 깨지지 않는다.

## Why

- live read adapter는 Python 함수와 CLI로만 연결되어 있어 브라우저 경로에서는 아직 사용할 수 없다.
- production API server/auth를 만들기 전, local runtime에서 안전하게 source switching을 검증해야 한다.

## Scope

- 포함:
  - fixture server source mode option
  - source mode health metadata
  - live missing-config HTTP error mapping
  - auto mode fixture fallback runtime smoke
  - tests and verification updates
  - docs/task handoff 갱신
- 제외:
  - production API deployment
  - auth/RBAC
  - write endpoint
  - new DB schema or benchmark changes
  - broad live endpoint expansion

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/fixture_server.py`
  - `tests/test_frontend_fixture_server.py`
  - `scripts/verify_frontend_fixture_server.sh`
  - `docs/frontend-fixture-server.md`
  - `docs/frontend-api-adapter.md`
  - `docs/frontend-architecture.md`
  - `docs/apps-web-scaffold.md`
  - `docs/verification-plan.md`
  - `docs/tasks/frontend-api-runtime-source-mode/`
- 수정 금지 파일:
  - DB migrations
  - secrets/env files
  - benchmark math
  - write endpoint implementation
  - broker/order integration
- 검증에 사용할 명령:
  - `bash -n scripts/verify_frontend_fixture_server.sh`
  - `bash scripts/verify_frontend_fixture_server.sh`
  - `bash scripts/verify_frontend_live_read_adapter.sh`
  - `bash scripts/verify_frontend_detail_routes.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-runtime-source-mode`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - source mode aware local HTTP runtime
  - regression tests
  - runtime verification script update
  - documentation update
  - task contract/plan/handoff/review

## Completion Criteria

- [x] default fixture HTTP behavior remains unchanged.
- [x] `--source auto` serves fixture data when DB config is absent.
- [x] `--source live` returns stable unavailable error when DB config is absent.
- [x] health payload exposes source mode.
- [x] method boundary remains read-only.
- [x] docs and handoff are updated.
- [x] harness verification passes.

## Risks

- local runtime still has no auth/RBAC, so it must stay local-only/read-only.
- live source currently supports only the live adapter pilot endpoints.
- production API latency/connection pooling remains future work.
