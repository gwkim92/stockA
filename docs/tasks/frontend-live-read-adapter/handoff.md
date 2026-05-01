# Session Handoff

## Active Task

- 이름: frontend-live-read-adapter
- 담당: Codex
- 날짜: 2026-05-01

## Current Status

- 완료:
  - 작업 계약과 구현 계획을 만들었다.
  - `src/stockanalysis/frontend/live_adapter.py`를 추가했다.
  - `api_adapter get --source fixture|live|auto`를 추가했다.
  - remediation ticket report와 portfolio outcome coverage report를 frontend DTO로 변환한다.
  - DB config가 없는 경우 `--source live`는 `FrontendLiveReadUnavailable` error JSON을 반환한다.
  - DB config가 없는 경우 `--source auto`는 fixture로 fallback한다.
  - report payload에 frontend DTO 변환용 `instrument_id` additive field를 추가했다.
  - unit tests, verification script, docs를 갱신했다.
- 막힌 점:
  - 아직 없음.

## Files Touched

- 생성:
  - `docs/tasks/frontend-live-read-adapter/contract.md`
  - `docs/tasks/frontend-live-read-adapter/plan.md`
  - `docs/tasks/frontend-live-read-adapter/handoff.md`
  - `docs/tasks/frontend-live-read-adapter/review.md`
  - `scripts/verify_frontend_live_read_adapter.sh`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
- 수정:
  - `README.md`
  - `docs/apps-web-scaffold.md`
  - `docs/frontend-api-adapter.md`
  - `docs/frontend-api-contract.md`
  - `docs/frontend-architecture.md`
  - `docs/portfolio-outcome-coverage-report.md`
  - `docs/portfolio-remediation-ticket-report.md`
  - `docs/verification-plan.md`
  - `src/stockanalysis/frontend/api_adapter.py`
  - `src/stockanalysis/performance/coverage.py`
  - `src/stockanalysis/signal/portfolio_remediation_ticket.py`
  - `tests/test_frontend_api_adapter.py`

## Decisions

- production API server를 바로 만들지 않고 read adapter pilot부터 만든다.
- live source는 `psql` command executor를 재사용한다.
- 지원 endpoint는 remediation tickets와 portfolio coverage로 제한한다.
- DB config가 없을 때는 `auto` source만 fixture fallback을 허용하고, `live` source는 실패시킨다.
- portfolio coverage의 default measurement end date는 `asOfDate + 31 days`로 계산한다.
- live adapter는 production API server가 아니라 Python read boundary다.

## Verification Already Run

- `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter -v`: 통과
- `PYTHONPATH=src python3 -m unittest tests.test_frontend_api_adapter -v`: 통과
- `bash -n scripts/verify_frontend_live_read_adapter.sh`: 통과
- `bash scripts/verify_frontend_live_read_adapter.sh`: 통과
- `bash scripts/verify_frontend_fixture_server.sh`: 통과
- `bash scripts/verify_frontend_detail_routes.sh`: 통과
- `PYTHONPATH=src python3 -m unittest tests.test_portfolio_outcome_coverage_report -v`: 통과
- `PYTHONPATH=src python3 -m unittest tests.test_portfolio_remediation_ticket -v`: 통과
- `git diff --check`: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-live-read-adapter`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음

## Still Unverified

- actual Postgres runtime smoke for frontend live adapter source mode

## Exact Next Step

- exact next step: `frontend-api-runtime-source-mode` task를 만들고 fixture server 또는 별도 local API server에 `fixture/live/auto` source mode를 연결한다.
- 다음 세션은 이것부터 시작: `apps/web`가 여전히 fixture server를 기본 source로 쓰므로, 브라우저 경로에서 live/auto source를 안전하게 선택할 API runtime boundary를 설계한다.

## Risks

- live pilot 범위가 2개 endpoint라 나머지 endpoint는 fixture 상태로 남는다.
- actual DB runtime smoke는 별도 Docker pipeline까지 묶으면 시간이 커지므로 이번 task는 fake executor unit test와 CLI fallback smoke 중심으로 검증한다.
- `apps/web`은 아직 fixture server를 기본 source로 사용한다. live/auto source를 브라우저 경로에 연결하려면 API runtime 단계가 필요하다.
