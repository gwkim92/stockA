# market-cycle-intelligence-decision-focus-v1 Handoff

## Current Status

- status: implemented_locally_pending_verification
- in progress: intelligence, cycle map, and market map copy now avoid internal/process wording and lead with decision checkpoints; local verification and EC2 deploy remain.
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

- exact next step: run local typecheck/build/AWH/diff checks, commit, push to `develop`, deploy to EC2, and route-smoke `/intelligence`, `/cycle-map`, `/market-map`.
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task market-cycle-intelligence-decision-focus-v1`
- `git diff --check`

## Remaining Risk

- This pass changes wording and first-read framing only. It does not redesign chart composition, add new analytics, or change recommendation scoring.
