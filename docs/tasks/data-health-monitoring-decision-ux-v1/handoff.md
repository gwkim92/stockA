# data-health-monitoring-decision-ux-v1 handoff

## Status

- current status: completed.
- completed: task contract created.
- completed: `/data-health` first-screen and major monitoring sections now use Korean user-facing decision language.
- completed: EC2 deployment and route/content smoke passed.

## Changes

- added top decision cards for service access, automated collection, data/AI quality, and investment boundary.
- translated visible monitoring copy for recommendation weight, broker/order, paper validation, thesis, outcome, feedback, calibration, cadence, router, child runner, source, coverage, active, quality eval, and systemd-like terms.
- kept detailed operator logs available under collapsed detail panels while keeping the primary page focused on what the user should check.
- did not change scheduler cadence, pipeline runners, DB/API contracts, recommendation weights, benchmark, portfolio positions, or broker/order boundaries.

## Verification

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-monitoring-decision-ux-v1`
- passed: EC2 deploy from `origin/codex/local-mvp-runtime-aws-bootstrap`, Next build, and `stockanalysis-web.service` restart.
- passed: `curl http://127.0.0.1:13000/data-health` returned 200 and content smoke found required Korean terms with no `EC2 systemd`, `추천 weight`, `paper validation`, `action router`, `child runner`, `quality eval`, or `source blocker`.
- passed: Playwright snapshot top-level smoke found `데이터 상태`, `추천 산식·주문 차단`, `자동 수집 작동 중` and no blocked jargon terms.

## Exact Next Step

- exact next step: continue the page-by-page UX refactor with `/performance`, because it still needs a clearer user-facing explanation of recommendation outcome, attribution, and what can or cannot change the scoring policy.

## Notes

- 화면 가시성 개선만 수행한다.
- 추천 weight, broker/order boundary, scheduler cadence, pipeline runners는 변경하지 않는다.
- commits: `e3a9ada1`, `59219567`, `7897e2d2`, `e14a4d68`.
