# market-cycle-intelligence-decision-focus-v1 Handoff

## Current Status

- status: implemented_and_ec2_smoked
- completed: intelligence, cycle map, and market map copy now avoid internal/process wording and lead with decision checkpoints; local verification, GitHub push, EC2 deploy, EC2 route smoke, and local tunnel smoke passed.
- branch: `develop`

## What Changed

- `/intelligence` now uses `뉴스 근거` and frames news clusters as investment evidence, blocked evidence, and recommendation impact.
- `/cycle-map` now describes top-down flow inspection without `자동 매수 신호`, `뉴스·AI`, or AI-process wording.
- `/market-map` now labels the first lane as market checkpoints: indicator reliability, price pressure, upper regime, recommendation boundary.

## Boundaries Preserved

- API contracts unchanged.
- Database schema unchanged.
- Scheduler cadence unchanged.
- Recommendation scoring weights unchanged.
- Benchmark definitions, portfolio positions, paper records, broker/order boundary, and live trading unchanged.

## Verification To Run

- exact next step: continue the UX/UI refactor with layout-level density and visual hierarchy work, starting with the repeated card grids on `/intelligence`, `/cycle-map`, `/market-map`, and then move to `/events` and `/events/classification`.
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task market-cycle-intelligence-decision-focus-v1`
- `git diff --check`

## Verification Evidence

- local passed: `cd apps/web && npm run typecheck`
- local passed: `cd apps/web && npm run build`
- local passed: `git diff --check`
- local passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task market-cycle-intelligence-decision-focus-v1`
- pushed commit: `713c8b20`
- EC2 deployed commit: `713c8b20`
- EC2 active services: `stockanalysis-web.service`, `stockanalysis-frontend-api.service`
- EC2 route smoke passed: `/intelligence`, `/cycle-map`, `/market-map`
- local tunnel `http://127.0.0.1:13000` route smoke passed for the same three routes.
- forbidden user-facing terms absent on smoke routes: `뉴스·AI`, `AI 해석`, `AI 근거`, `추천 weight`, `파이프라인`

## Remaining Risk

- This pass changes wording and first-read framing only. It does not redesign chart composition, add new analytics, or change recommendation scoring.
