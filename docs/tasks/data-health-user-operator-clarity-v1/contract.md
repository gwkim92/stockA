# data-health-user-operator-clarity-v1 Contract

## Task Request

- request: Continue the UX wording cleanup on `/data-health`.
- context: News and AI evidence pages now use clearer user-facing wording. `/data-health` still mixes investor-facing status with operator diagnostics and older terms such as `보유검토`, `보유 검토`, `검토 후보`, `검토서`, and `페이퍼`.

## Goal

- goal: Make `/data-health` read as a status control room with two layers:

`사용자용 상태 요약 → 수집/분석/품질/투자 경계 → 접힌 운영 진단`

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/data-health/page.tsx`
  - `docs/tasks/data-health-user-operator-clarity-v1/*`

## Invariants

- Do not change API DTO contracts.
- Do not change scheduler cadence.
- Do not change recommendation scoring weights.
- Do not change benchmark definitions, portfolio positions, recommendations, theses, or paper outcomes.
- Do not enable broker submit, automatic orders, automatic rebalancing, or write APIs.
- Do not rename backend fields or raw diagnostic keys.

## Scope

- Replace user-facing `보유검토`/`보유 검토` with `보유 상태` or `보유 상태 판단`.
- Replace `검토 후보` with `확인 대상` where it describes UI status rather than an internal model field.
- Replace `검토서` with `추천 상세` or `상세 근거`.
- Replace user-facing `페이퍼` shorthand with `가상 매매`.
- Keep raw operator diagnostics available in collapsed sections.

## Verification

- verification command: `rg -n "보유검토|보유 검토|검토 후보|검토서|페이퍼" apps/web/src/app/data-health/page.tsx`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: route smoke for `/data-health`.
- verification command: browser text smoke for `/data-health`.
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task data-health-user-operator-clarity-v1`
