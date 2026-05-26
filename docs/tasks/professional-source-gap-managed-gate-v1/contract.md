# professional-source-gap-managed-gate-v1 Contract

## Task Request

- request: Separate managed professional source limitations from unresolved source-gap gates.
- context: EC2 currently shows `professional_source_gap_attention` because EROK lacks SEC us-gaap facts, but EROK is already blocked from professional decision use and paper validation until periodic filings or a safe prospectus parser exist. That should remain visible, but it should not behave like an unresolved operating gate.

## Goal

- goal: Keep source limitations visible while only opening `professional_source_gap_attention` for actionable or unsafe gaps.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `docs/tasks/professional-source-gap-managed-gate-v1/*`
  - `docs/plans/2026-05-27-professional-source-gap-managed-gate-v1.md`

## Invariants

- Do not hide source gaps from `professional_source_gap_prioritization`.
- Do not remove existing gate ids for genuinely unresolved conditions.
- Do not change recommendation score weights.
- Do not change benchmark definitions.
- Do not mutate portfolio positions, recommendations, theses, or paper outcomes.
- Do not enable broker submit, automatic orders, or automatic rebalancing.

## Scope

- Add a deterministic `attention_required` policy to the professional source gap payload.
- Treat durable excluded operating-company source blockers as managed only when professional decision use and paper validation are already blocked.
- Treat fund/company model not-applicable rows as managed when missing source layer count is zero.
- Continue opening `professional_source_gap_attention` for unguarded source blockers, coverage gaps, fund source gaps, or high-priority gaps that still feed decisions.
- Render managed source limitations as source limits rather than broken data.

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task professional-source-gap-managed-gate-v1`
