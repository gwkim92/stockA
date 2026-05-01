# Session Handoff

## Active Task

- 이름: frontend-api-adapter-foundation
- 담당: Codex
- 날짜: 2026-05-01

## Current Status

- 완료:
  - read-only frontend API fixture adapter를 추가했다.
  - adapter CLI `list`와 `get --path`를 추가했다.
  - unit tests와 verification script를 추가했다.
  - README, verification plan, frontend docs를 갱신했다.
- 막힌 점:
  - actual HTTP server와 frontend scaffold는 이번 범위 밖이다.

## Files Touched

- 생성:
  - `docs/plans/2026-05-01-frontend-api-adapter-foundation.md`
  - `docs/frontend-api-adapter.md`
  - `docs/tasks/frontend-api-adapter-foundation/contract.md`
  - `docs/tasks/frontend-api-adapter-foundation/plan.md`
  - `docs/tasks/frontend-api-adapter-foundation/handoff.md`
  - `docs/tasks/frontend-api-adapter-foundation/review.md`
  - `src/stockanalysis/frontend/__init__.py`
  - `src/stockanalysis/frontend/api_adapter.py`
  - `tests/test_frontend_api_adapter.py`
  - `scripts/verify_frontend_api_adapter.sh`
- 수정:
  - `README.md`
  - `pyproject.toml`
  - `docs/frontend-architecture.md`
  - `docs/frontend-api-contract.md`
  - `docs/verification-plan.md`
  - `docs/tasks/frontend-api-adapter-foundation/contract.md`
  - `docs/tasks/frontend-api-adapter-foundation/handoff.md`
  - `docs/tasks/frontend-api-adapter-foundation/review.md`

## Decisions

- adapter는 exact API path matching으로 시작한다.
- source of truth는 `docs/api/frontend/contract-index.json`이다.
- actual HTTP API server와 frontend scaffold는 이번 작업에서 만들지 않는다.
- unknown path는 `FrontendApiPathNotFound` error JSON과 non-zero exit code를 반환한다.

## Verification Already Run

- `bash -n scripts/verify_frontend_api_adapter.sh`: 통과
- `PYTHONPATH=src python3 -m unittest tests.test_frontend_api_adapter -v`: 통과
- `PYTHONPATH=src python3 -m stockanalysis.frontend.api_adapter get --path /api/dashboard/today`: 통과
- `bash scripts/verify_frontend_api_adapter.sh`: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-adapter-foundation`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음

## Still Unverified

- HTTP fixture server
- live DB adapter
- `apps/web` scaffold
- browser smoke
- auth/RBAC

## Exact Next Step

- 다음 세션은 이것부터 시작: `frontend-fixture-server-foundation`으로 adapter를 local HTTP endpoint로 노출하거나, `apps-web-scaffold`로 fixture-only UI shell을 만든다.

## Risks

- fixture adapter는 live DB freshness를 보장하지 않는다.
- query normalization은 아직 없다.
- exact path matching이라 query parameter order가 바뀌면 resolve되지 않는다.
