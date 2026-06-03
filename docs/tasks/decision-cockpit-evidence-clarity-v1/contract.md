# decision-cockpit-evidence-clarity-v1 Contract

## Task Request

- request: Improve the main cockpit and AI evidence wording/structure so a Korean user can understand what to inspect without reading operator-style implementation notes.
- context: Operational gates are currently closed, but the user-facing experience still mixes monitoring language, AI pipeline descriptions, and investment judgment steps. The first screen and AI evidence detail need clearer decision hierarchy.

## Goal

- goal: Make the home page and AI evidence detail explain the judgment path in user language: `수집 상태 → 새 근거 → 종목/흐름 연결 → 추천/보유 영향 → 페이퍼/주문 경계`.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `apps/web/src/lib/korean-labels.ts`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/decision-cockpit-evidence-clarity-v1/*`

## Invariants

- Do not change API DTO contracts.
- Do not change recommendation scoring weights.
- Do not change benchmark definitions, portfolio positions, recommendations, theses, or paper outcomes.
- Do not enable broker submit, automatic orders, or automatic rebalancing.
- Do not hide operational failures; move operator-style details to the appropriate context instead of deleting risk signals.

## Scope

- Rewrite confusing labels such as action-less `검토 가능` into concrete states.
- Add a compact home-page “오늘 판단 순서” panel that distinguishes evidence inspection from order execution.
- Improve AI evidence detail trace copy so it shows source, Korean translation, AI result, validator, propagation, and recommendation link as a reviewable chain.
- Keep the visual language consistent with the existing site while reducing duplicate explanatory text.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: route smoke for `/`, `/ai-evidence`, and one `/ai-evidence/{id}`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task decision-cockpit-evidence-clarity-v1`
