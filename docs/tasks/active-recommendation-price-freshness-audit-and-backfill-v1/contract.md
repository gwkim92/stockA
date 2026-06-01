# active-recommendation-price-freshness-audit-and-backfill-v1 Contract

## Task Request

- request: EC2 live DB에서 active recommendation 종목의 가격 데이터가 최신 가격일보다 오래된 문제를 복구하고, 같은 문제가 다시 묻히지 않도록 `/api/data-health`와 `/data-health`에 노출한다.

## Goal

- goal: active recommendation에 연결된 종목별 최신 가격일을 global latest price date와 비교해 stale/missing 상태를 자동 판정하고, 필요하면 market-price free backfill로 보강할 수 있다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/active-recommendation-price-freshness-audit-and-backfill-v1/*`
  - repo-outside EC2 runtime watchlist/artifact files

## Invariants

- Do not change recommendation scoring weights.
- Do not change benchmark definitions, portfolio positions, thesis state, paper validation records, broker/order flow, or live trading.
- Do not hide stale active recommendation price data as healthy.
- Do not store provider API keys or runtime env values in the repo.

## Scope

- Add `active_recommendation_price_freshness` to data-health live payload.
- Add an open gate detail when active recommendation symbols are stale/missing versus the latest observed market price date.
- Render a Korean `/data-health` card that explains affected symbols, latest price date, and read-only order boundary.
- Backfill stale active recommendation symbols on EC2 through the existing free market price provider runner.

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task active-recommendation-price-freshness-audit-and-backfill-v1`
- verification command: `git diff --check`
- EC2 smoke: `/api/data-health` exposes active recommendation price freshness and `/data-health` renders it.

## Done Criteria

- [x] `/api/data-health` includes active recommendation price freshness summary and stale symbol examples.
- [x] `/data-health` explains active recommendation price freshness in Korean.
- [x] Stale/missing active recommendation price data is visible as an attention gate.
- [x] EC2 stale symbols are backfilled where the free provider can return data.
- [x] Verification commands pass or unresolved provider/source limitations are documented.
