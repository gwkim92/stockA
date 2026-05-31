# performance-copy-polish-v3 handoff

## Status

- current status: completed.
- completed: task contract created.
- completed: `/performance` copy and labels now avoid raw internal terms in the main user-facing flow.
- completed: EC2 deployment and route/content smoke passed.

## Changes

- changed contribution display from raw `bps` to percentage-point style `%p`.
- translated performance page copy around `thesis`, `outcome window`, `weight`, `quality gate`, `source_run_id`, methodology, and attribution component labels.
- kept recommendation links, thesis links, coverage links, and read-only performance evidence sections intact.
- did not change scoring weights, benchmark, portfolio positions, outcome records, API DTOs, DB schema, or broker/order boundaries.

## Verification

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task performance-copy-polish-v3`
- passed: `git diff --check`
- passed: EC2 deploy from `origin/codex/local-mvp-runtime-aws-bootstrap`, Next build, and `stockanalysis-web.service` restart.
- passed: `curl http://127.0.0.1:13000/performance` returned 200 and content smoke found `성과 판정판`, `추천 산식 가중치 변경`, `성과 측정창`, `품질 기준`, `%p` with no `추천 weight`, `자동 weight`, `outcome window`, `quality gate`, `source_run_id`, `bps`, or `개 thesis`.
- passed: Playwright snapshot smoke for `/performance` found required Korean terms and no blocked jargon.

## Exact Next Step

- exact next step: continue the page-by-page UX refactor with `/events`, because raw event/classification pages still need clearer user-facing hierarchy.

## Notes

- frontend visibility only.
- recommendation weights, broker/order boundary, portfolio positions, benchmark, and outcome records are not changed.
- commit: `74e0cab8`.
