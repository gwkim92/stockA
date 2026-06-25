# portfolio-return-timeseries-and-market-heatmap-v1 Handoff

## Current Status

- implemented locally: stock movement heatmap, portfolio return distribution, and data-health coverage matrix are wired to existing DTOs.
- verification passed locally: frontend unit tests, typecheck/build, frontend API contract, roadmap verification, AWH task verification, and browser smoke against EC2 FastAPI data via local Next.
- not yet deployed: commit, push, EC2 `develop` pull, service restart, and EC2 route smoke remain.

## Notes

- Existing DTOs already contain the data needed for this slice.
- `/api/stocks` has `latest_price.change_pct`.
- `/api/portfolio/.../coverage` has `market_value`, `cost_basis`, `unrealized_pnl`, and position metadata.
- `/api/data-health` has `pipeline_runs`, `freshness`, provider budget, and active recommendation price freshness.
- Added shared movement helpers in `apps/web/src/lib/presentation/returns.ts`.
- Added `/stocks` heatmap component in `apps/web/src/app/stocks/StockMovementHeatmap.tsx`.
- Extended portfolio coverage with a return distribution panel in `apps/web/src/components/portfolio/PortfolioReturnSummaryPanel.tsx`.
- Extended data health overview with a source-to-screen coverage matrix in `apps/web/src/components/operations/DataHealthOverview.tsx`.
- Screenshots captured under `/tmp/stockanalysis-visual-qa-portfolio-return-v1/`.
- exact next step: commit/push the feature branch, merge to `develop`, deploy to EC2, and smoke `/stocks`, `/portfolio/coverage`, `/data-health` on `http://127.0.0.1:13000`.
