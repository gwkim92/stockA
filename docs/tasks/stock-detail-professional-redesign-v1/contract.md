# stock-detail-professional-redesign-v1 Contract

## Request

- `/stocks/[symbol]`을 전문 종목 분석서 구조로 재구성한다.

## Scope

- Split route-local components under `apps/web/src/app/stocks/[symbol]/_components/`.
- Top section always shows product type, previous-day move, current price, holding status, average cost, unrealized PnL, and analysis status.
- Company layout differs from ETF/fund layout.
- Toss data is labeled as broker reality data; global data is labeled as analysis reference data.

## Invariants

- No backend DTO change.
- No score/schema/portfolio/broker boundary changes.

## Verification

- `/stocks/AAPL` and `/stocks/SPY` or `/stocks/QQQ` render different analysis structures.
- No investor-facing forbidden terms.
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `cd apps/web && npm run test:e2e`
- AWH verify for this task.
