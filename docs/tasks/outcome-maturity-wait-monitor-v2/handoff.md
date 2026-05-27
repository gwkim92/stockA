# outcome-maturity-wait-monitor-v2 Handoff

## Status

- completed: local verification, EC2 deploy, EC2 API smoke, EC2 route smoke, and local tunnel smoke passed.

## Current Decision

- Add a derived data-health DTO rather than a new backend runner. Existing outcome maturity and feedback calibration artifacts already hold the source of truth.
- Keep the monitor read-only. It can explain when to wait or when to run calibration, but it must not mutate scoring weights or execute broker/order flows.

## Next Step

- exact next step: keep waiting until the 2026-06-20 recommendation outcome window, then run the already-routed outcome calibration; do not start `manual-weight-review-pilot-v1` until mature evidence exists.

## Verification So Far

- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task outcome-maturity-wait-monitor-v2`
- passed: `git diff --check`
- passed on EC2: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- passed on EC2: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m compileall -q src tests`
- passed on EC2: `cd apps/web && npm run typecheck && npm run build`
- passed on EC2: `systemctl is-active stockanalysis-frontend-api.service stockanalysis-web.service` returned `active active`.
- passed on EC2: `/api/data-health.outcome_maturity_wait_monitor.status=managed_wait`, recommendation next due `2026-06-20`, next due count `19`, portfolio feedback maturity `2026-06-24`, mature decision gap `10`, `weight_review_blocked=true`, `manual_weight_review_allowed=false`, `automatic_weight_change_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`.
- passed on EC2: `/data-health` rendered `성과 성숙 대기 모니터`, `추천 outcome`, `포트폴리오 feedback`, `2026-06-20`, `2026-06-24`, `weight 검토`, and `자동 변경 금지`.
- passed locally through the EC2 tunnel: `http://127.0.0.1:13000/data-health` rendered the same strings.

## Risks

- This monitor improves visibility only. It does not create new outcome samples.
- Weight review remains blocked until due outcome windows and mature feedback samples exist.
