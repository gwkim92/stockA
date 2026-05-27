# outcome-maturity-wait-monitor-v2 Contract

## Task Request

- request: 추천 outcome window와 포트폴리오 feedback outcome window를 한 곳에서 보여주고, 성과 표본이 성숙하기 전까지 추천 weight 검토가 왜 막혀 있는지 명확히 고정한다.

## Goal

- goal: `/api/data-health`와 `/data-health`가 `outcome_maturity_wait_monitor`를 노출하여 추천 outcome 다음 측정일, 포트폴리오 feedback 성숙 예정일, 차단된 weight review 이유, 다음 실행 조건을 한 카드에서 설명한다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/outcome-maturity-wait-monitor-v2/*`

## Invariants

- Do not change recommendation scoring weights.
- Do not run or schedule calibration early.
- Do not change benchmark definitions, portfolio positions, broker/order flow, live trading, or paper execution.
- Do not hide immature outcome state as healthy evidence. It must remain visible as managed wait.

## Scope

- Add a derived read-only `outcome_maturity_wait_monitor` data-health payload.
- Combine recommendation outcome maturity, recommendation outcome due action router, portfolio review feedback calibration, and weight review readiness.
- Render a Korean `/data-health` section that says when to wait, what to run when due, and why weight review remains blocked.

## Verification

- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task outcome-maturity-wait-monitor-v2`
- verification command: `git diff --check`

## Done Criteria

- [ ] `/api/data-health` includes `outcome_maturity_wait_monitor`.
- [ ] Monitor includes recommendation next due date, portfolio feedback maturity date, weight review block reason, and read-only order boundary.
- [ ] `/data-health` renders the combined wait monitor in Korean.
- [ ] Local verification passes.
- [ ] EC2 route smoke confirms live rendering.
