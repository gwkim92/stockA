# decision-cockpit-outcome-wait-visibility-v1 Handoff

## Status

- completed: local implementation, GitHub push, EC2 deploy, web service restart, EC2 route smoke, and local tunnel smoke are complete.
- current status: completed.

## Current Decision

- Use existing `/api/data-health.outcome_maturity_wait_monitor` on the home page.
- This is UX visibility only. It must not mutate recommendation weights, benchmark definitions, portfolio positions, paper execution, broker submit, or order flow.

## Next Step

- exact next step: keep waiting until the 2026-06-20 recommendation outcome window and 2026-06-24 portfolio feedback maturity window; do not start manual weight review or scoring weight changes before mature evidence exists.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task decision-cockpit-outcome-wait-visibility-v1`
- passed: `git diff --check`
- passed on EC2: `cd /opt/stockanalysis/app/apps/web && npm run typecheck && npm run build`
- passed on EC2: `systemctl is-active stockanalysis-web.service` returned `active`.
- passed on EC2: `/` rendered `성과 성숙`, `추천 outcome`, `포트폴리오 feedback`, `weight 검토`, and `주문 제출 차단`.
- passed locally through the EC2 tunnel: `http://127.0.0.1:13000/` rendered the same outcome wait strings.

## Risks

- This does not create new outcome samples. It only makes the managed wait state visible earlier in the decision flow.
