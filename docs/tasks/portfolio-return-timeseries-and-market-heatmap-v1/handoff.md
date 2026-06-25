# portfolio-return-timeseries-and-market-heatmap-v1 Handoff

## Current Status

- implemented locally: stock movement heatmap, portfolio return distribution, and data-health coverage matrix are wired to existing DTOs.
- deployed to EC2: `develop` is at `1c52d7b7`, EC2 pulled the same commit, Next build passed, and `stockanalysis-web`, `stockanalysis-web-public-13000`, `stockanalysis-frontend-api` are active.
- verification passed: frontend unit tests, typecheck/build, frontend API contract, roadmap verification, AWH task verification, local browser smoke against EC2 FastAPI data, and EC2 `13000` browser smoke.

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
- During local dev smoke, an existing duplicate React key warning for `weak_propagation_evidence-1258` was found and fixed in `apps/web/src/app/data-health/page.tsx`.
- EC2 route smoke confirmed `/stocks`, `/portfolio/coverage`, and `/data-health` render the new Korean labels with horizontal overflow `0` on 375px and 1280px.
- exact next step: continue the broader workspace redesign work; the remaining issue is not this slice but the older long-form screens that still feel dense and need component-level pruning.
