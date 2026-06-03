# data-health-intelligence-wording-clarity-v1 Contract

## Task Request

- request: Continue the UX wording cleanup on `/data-health` and `/intelligence`.
- context: Home and AI evidence detail were cleaned up, but data-health and intelligence still contain action-less labels such as `검토 가능`, `별도 검토 가능`, and internal terms such as `AI 상세`.

## Goal

- goal: Make `/data-health` and `/intelligence` show concrete states and next screens, not vague review/ops phrases. A user should understand whether the system is healthy, waiting, blocked, or showing evidence without assuming a missing manual review button exists.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/app/intelligence/page.tsx`
  - `docs/tasks/data-health-intelligence-wording-clarity-v1/*`

## Invariants

- Do not change API DTO contracts.
- Do not change scheduler cadence.
- Do not change recommendation scoring weights.
- Do not change benchmark definitions, portfolio positions, recommendations, theses, or paper outcomes.
- Do not enable broker submit, automatic orders, or automatic rebalancing.

## Scope

- Replace action-less `검토 가능` / `별도 검토 가능` labels with concrete status labels such as `성과 표본 충족`, `대기`, or `전문 근거 충족`.
- Rename internal/awkward buttons such as `AI 상세` to user-facing labels such as `근거 상세`.
- Keep technical details accessible, but label collapsed operator details as optional operational records.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: route smoke for `/data-health` and `/intelligence`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task data-health-intelligence-wording-clarity-v1`

