# data-health-intelligence-wording-clarity-v1 Handoff

## Current Status

- in progress: local implementation and local verification are complete; EC2 deploy/route smoke is pending.

## Decisions

- This is a wording/UX clarity task only.
- Preserve `/data-health` as the detailed operational page, but make collapsed technical sections clearly optional.
- Avoid labels that imply a missing manual approval/review control.

## Verification

- passed: local text scan found no `검토 가능`, `별도 검토 가능`, `상세 검토 가능`, `AI 상세`, `운영자용`, or `검토 필요` in `data-health`/`intelligence`.
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- passed: `git diff --check`
- passed: EC2 services are active and internal `/data-health`, `/intelligence`, and `/__health` returned HTTP 200 before deploy.
- passed: local tunnel restored on `127.0.0.1:13000` with ssh PID `61058`.

## Next Step

- exact next step: run AWH verify, commit/push, deploy to EC2, rebuild/restart Next.js, and route-smoke `/data-health` and `/intelligence` with the updated wording.
