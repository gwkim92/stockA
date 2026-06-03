# stock-recommendation-detail-professional-clarity-v1 Contract

## Task Request

- request: Continue the UX wording cleanup on `/stocks`, `/stocks/[symbol]`, and `/recommendations/[recommendationId]`.
- context: The previous slice cleaned `/cycle-map`, `/recommendations`, and `/paper-trading`, but stock and recommendation detail pages still contain vague review labels such as `추천 검토서`, `AI 검토 통과`, `검토 입력 가능`, and `보유 검토`.

## Goal

- goal: Make stock and recommendation detail pages read like investment evidence screens, not unfinished manual review tools. The user should see evidence status, professional analysis coverage, paper validation input status, and read-only order boundary clearly.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/stocks/page.tsx`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `docs/tasks/stock-recommendation-detail-professional-clarity-v1/*`

## Invariants

- Do not change API DTO contracts.
- Do not change scheduler cadence.
- Do not change recommendation scoring weights.
- Do not change benchmark definitions, portfolio positions, recommendations, theses, or paper outcomes.
- Do not enable broker submit, automatic orders, or automatic rebalancing.

## Scope

- Replace ambiguous `검토` labels with concrete evidence/status labels where no manual action control exists.
- Keep professional analysis, financial model, valuation, news/AI evidence, thesis, and paper trading boundaries visible.
- Preserve route structure and server component data fetching.

## Verification

- verification command: `rg -n "추천 검토서|AI 검토|검토 입력 가능|검토 대기|추천 검토|보유 검토|검토 전" apps/web/src/app/stocks/page.tsx apps/web/src/app/stocks/[symbol]/page.tsx apps/web/src/app/recommendations/[recommendationId]/page.tsx`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: route smoke for `/stocks`, `/stocks/SPY`, and a representative recommendation detail route.
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task stock-recommendation-detail-professional-clarity-v1`
