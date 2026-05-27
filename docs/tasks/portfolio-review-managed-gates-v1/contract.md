# portfolio-review-managed-gates-v1 Contract

## Task Request

- request: Separate unmanaged portfolio drift/review blockers from already managed review decisions.
- context: Current EC2 data-health has `benchmark_drift_quality_attention` and `portfolio_review_decision_history_attention` even though the drift decisions have been persisted, order boundaries are read-only, and the action router is waiting for the outcome observation window.

## Goal

- goal: Keep portfolio concentration and review decisions visible, but only keep open gates when evidence is missing, unsafe, or not yet routed into the review lifecycle.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `docs/tasks/portfolio-review-managed-gates-v1/*`
  - `docs/plans/2026-05-27-portfolio-review-managed-gates-v1.md`

## Invariants

- Do not remove benchmark drift or portfolio review decision evidence from the payload or UI.
- Do not change recommendation score weights.
- Do not change benchmark definitions or benchmark holdings.
- Do not mutate portfolio positions, recommendations, theses, or outcome rows.
- Do not enable broker submit, automatic orders, or automatic rebalancing.

## Scope

- Add `attention_required` and managed review metadata to benchmark drift quality and portfolio review decision history payloads.
- Treat current high drift as managed only when persisted review decisions exist and the action router is in a safe wait/current-complete state.
- Keep gates open for missing/partial/stale benchmark source, missing decision history, unsafe router states, or contradictions.
- Update Korean `/data-health` wording to show "managed review" instead of implying broken data.

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-review-managed-gates-v1`
