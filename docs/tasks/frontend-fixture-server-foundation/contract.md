# Task Contract

## Task

- 이름: frontend-fixture-server-foundation
- 요청: frontend API fixture adapter를 local read-only HTTP endpoint로 노출한다.
- 담당: Codex
- 날짜: 2026-05-01

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `docs/api/frontend/contract-index.json`에 정의된 fixture API path를 HTTP GET으로 호출하면 contract-shaped JSON payload가 반환된다.

## Why

- 다음 `apps/web` scaffold가 Python 모듈을 직접 import하지 않고 browser fetch로 fixture payload를 사용할 수 있어야 한다.
- live DB adapter나 운영 API framework 결정 전에, UI 개발과 browser smoke를 시작할 최소 HTTP 경계가 필요하다.

## Scope

- 포함:
  - Python 표준 라이브러리 기반 local HTTP fixture server
  - `/__health`와 `/__endpoints` read endpoint
  - contract index exact path 기반 fixture response
  - stable JSON error response
  - tests
  - verification script
  - docs/task handoff 갱신
- 제외:
  - live DB query adapter
  - production API framework 선택
  - frontend scaffold
  - auth/RBAC
  - deployment config
  - write endpoint 구현

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `pyproject.toml`
  - `docs/plans/2026-05-01-frontend-fixture-server-foundation.md`
  - `docs/frontend-fixture-server.md`
  - `docs/frontend-api-adapter.md`
  - `docs/frontend-api-contract.md`
  - `docs/frontend-architecture.md`
  - `docs/tasks/frontend-fixture-server-foundation/`
  - `docs/verification-plan.md`
  - `src/stockanalysis/frontend/fixture_server.py`
  - `tests/test_frontend_fixture_server.py`
  - `scripts/verify_frontend_fixture_server.sh`
- 수정 금지 파일:
  - DB migrations
  - deployment secrets
  - scheduler activation artifacts
  - frontend scaffold directories
- 검증에 사용할 명령:
  - `bash -n scripts/verify_frontend_fixture_server.sh`
  - `bash scripts/verify_frontend_fixture_server.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-fixture-server-foundation`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - local frontend fixture HTTP server module
  - fixture server CLI
  - fixture server tests
  - fixture server verification script
  - fixture server docs
  - README/verification plan update
  - task contract/plan/handoff/review

## Completion Criteria

- [x] `/__health`가 contract version과 endpoint count를 반환한다.
- [x] `/__endpoints`가 fixture endpoint index를 반환한다.
- [x] known API path가 linked example JSON을 HTTP로 반환한다.
- [x] query string이 포함된 known API path가 exact match로 반환된다.
- [x] unknown path가 stable JSON 404를 반환한다.
- [x] non-read method가 stable JSON 405를 반환한다.
- [x] live DB, auth, frontend scaffold는 생성하지 않는다.
- [x] docs와 handoff가 갱신된다.
- [x] 하네스 검증이 통과한다.

## Risks

- fixture server는 live DB freshness를 보장하지 않는다.
- exact path matching이라 query parameter order가 바뀌면 resolve되지 않는다.
- 표준 라이브러리 서버는 local development fixture 용도이며 production API server가 아니다.
