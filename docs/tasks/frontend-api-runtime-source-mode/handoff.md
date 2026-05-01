# Session Handoff

## Active Task

- 이름: frontend-api-runtime-source-mode
- 담당: Codex
- 날짜: 2026-05-01

## Current Status

- 완료:
  - task contract와 plan을 만들었다.
  - `src/stockanalysis/frontend/fixture_server.py`에 `--source fixture|live|auto`를 추가했다.
  - default `fixture` source mode를 유지했다.
  - `/__health`와 `/__endpoints`에 `source_mode`를 추가했다.
  - `auto` source는 DB config가 없으면 fixture fallback한다.
  - `live` source는 DB config가 없으면 HTTP 503 `FrontendLiveReadUnavailable` error JSON을 반환한다.
  - write method boundary는 405 read-only 상태로 유지했다.
  - fixture server tests와 runtime smoke를 갱신했다.
- 막힌 점:
  - 아직 없음.

## Files Touched

- 생성:
  - `docs/tasks/frontend-api-runtime-source-mode/contract.md`
  - `docs/tasks/frontend-api-runtime-source-mode/plan.md`
  - `docs/tasks/frontend-api-runtime-source-mode/handoff.md`
  - `docs/tasks/frontend-api-runtime-source-mode/review.md`
- 수정:
  - `README.md`
  - `docs/apps-web-scaffold.md`
  - `docs/frontend-api-adapter.md`
  - `docs/frontend-architecture.md`
  - `docs/frontend-fixture-server.md`
  - `docs/verification-plan.md`
  - `scripts/verify_frontend_fixture_server.sh`
  - `src/stockanalysis/frontend/fixture_server.py`
  - `tests/test_frontend_fixture_server.py`

## Decisions

- fixture server 이름은 유지하되 read runtime source mode를 추가한다.
- 기본 source는 `fixture`로 유지한다.
- `auto`는 DB config가 없으면 fixture fallback한다.
- `live`는 DB config가 없으면 HTTP 503 stable error를 반환한다.
- unsupported live path는 HTTP 501로 매핑한다.
- production API server/auth/RBAC는 이번 범위 밖이다.

## Verification Already Run

- `PYTHONPATH=src python3 -m unittest tests.test_frontend_fixture_server -v`: 통과
- `bash scripts/verify_frontend_fixture_server.sh`: 통과
- `bash scripts/verify_frontend_live_read_adapter.sh`: 통과
- `bash -n scripts/verify_frontend_fixture_server.sh`: 통과
- `bash scripts/verify_frontend_detail_routes.sh`: 통과
- `git diff --check`: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-runtime-source-mode`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음

## Still Unverified

- actual DB-backed HTTP live success smoke

## Exact Next Step

- exact next step: `frontend-live-read-expansion` task를 만들고 daily cockpit, data health, event/theme, performance endpoint의 live DTO 지원 우선순위를 정한다.

## Risks

- runtime은 여전히 local/read-only 용도이며 production auth/RBAC 경계가 아니다.
- live source 지원 endpoint는 remediation tickets와 portfolio coverage로 제한된다.
