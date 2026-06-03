# cycle-recommendation-paper-wording-clarity-v1 Contract

## Task Request

- request: Continue the UX wording cleanup on `/cycle-map`, `/recommendations`, and `/paper-trading`.
- context: `/data-health` and `/intelligence` were cleaned up, but the cycle, recommendation, and paper trading pages still contain vague action-less review labels such as `AI 검토 통과`, `상세 검토 가능`, `후보 검토`, and `검토 기록`.

## Goal

- goal: Make the three pages distinguish evidence, candidate status, paper validation, and order boundary without implying a missing manual review button or live trading action.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/cycle-map/page.tsx`
  - `apps/web/src/app/recommendations/page.tsx`
  - `apps/web/src/app/paper-trading/page.tsx`
  - `docs/tasks/cycle-recommendation-paper-wording-clarity-v1/*`

## Invariants

- Do not change API DTO contracts.
- Do not change scheduler cadence.
- Do not change recommendation scoring weights.
- Do not change benchmark definitions, portfolio positions, recommendations, theses, or paper outcomes.
- Do not enable broker submit, automatic orders, or automatic rebalancing.

## Scope

- Replace `AI 검토` and `AI 판단` copy with `AI 검증`, `AI 근거`, or `뉴스·AI 근거`.
- Replace action-less `상세 검토 가능`, `검토 입력 부족`, and `추천 검토서` with concrete evidence and status wording.
- Replace paper trading copy that implies manual review controls with simulation, candidate, audit-record, and read-only boundary wording.

## Verification

- verification command: `rg -n "AI 검토|상세 검토 가능|검토 입력 부족|추천 검토서|후보 검토|읽기 전용 검토|검토 기록|AI 판단|추천 검토" apps/web/src/app/cycle-map/page.tsx apps/web/src/app/recommendations/page.tsx apps/web/src/app/paper-trading/page.tsx`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: route smoke for `/cycle-map`, `/recommendations`, and `/paper-trading`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task cycle-recommendation-paper-wording-clarity-v1`
