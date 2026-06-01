# data-health-cadence-aware-stale-policy-v1 Contract

## Task Request

- request: `/data-health`가 월요일 장 시작 전에도 금요일 장마감 daily job을 stale로 표시하는 false-positive를 고친다.

## Goal

- goal: daily data-operation job은 단순 경과시간이 아니라 `America/New_York` 기준 Mon-Fri 예정 실행 시각을 기준으로 최신성을 판단한다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/data-health-cadence-aware-stale-policy-v1/*`

## Invariants

- Do not change scheduler timer installation.
- Do not change command cadence definitions, recommendation scoring weights, benchmark definitions, portfolio positions, broker/order flow, or live trading.
- Do not hide a genuinely missed due daily run. If the latest expected Mon-Fri run is missing, it must remain stale/attention.
- Keep timezone fixed to `America/New_York`, matching operating-data scheduler installation.

## Scope

- Add cadence-aware latest-due logic for daily jobs in the data-health SQL.
- Keep intraday, weekly, and monthly stale policies unchanged.
- Document why the previous 36-hour rule caused a weekend/pre-open false-positive.

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task data-health-cadence-aware-stale-policy-v1`
- verification command: `git diff --check`
- EC2 smoke: `/api/data-health` no longer marks not-yet-due daily jobs stale before Monday evening New York time.

## Done Criteria

- [ ] SQL contains an explicit `America/New_York` latest-due calculation for daily jobs.
- [ ] Local tests/build pass.
- [ ] EC2 `/api/data-health` no longer opens `data_operations_artifact_runner` only because Friday post-market daily jobs are older than 36 hours before Monday's due time.
- [ ] Remaining open gates are documented separately.
