# market-portfolio-return-visibility-v1 handoff

## Current Status

- completed: Implementation, local verification, GitHub push, EC2 deployment, and route smoke are complete.

## Notes

- `/api/stocks`는 이미 `latest_price.change_pct`를 계산한다.
- `/api/portfolio/.../coverage`는 position별 `market_value`, `cost_basis`, `unrealized_pnl`을 제공한다.
- 이번 작업은 표시/집계 계층 변경이며 scoring, benchmark, portfolio position, broker boundary는 변경하지 않는다.
- implemented: Added typed presentation helpers for signed percent labels and portfolio return aggregation.
- implemented: Added reusable return badge and portfolio return summary panel.
- implemented: `/stocks`, `/stocks/[symbol]`, `/portfolio/coverage` now expose return/change visibility from existing DTO fields.
- verification: `cd apps/web && npm test -- --run` passed.
- verification: `cd apps/web && npm run typecheck` passed.
- verification: `cd apps/web && npm run build` passed.
- verification: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter tests.test_frontend_api_adapter` passed after restoring the API LLM/AI failure label contract.
- verification: `PYTHONPATH=src python3 -m compileall -q src tests` passed.
- verification: `bash scripts/verify_frontend_api_contract.sh` passed.
- verification: `bash scripts/verify_project_execution_roadmap.sh` passed.
- verification: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task market-portfolio-return-visibility-v1` passed.
- verification: `git diff --check` passed.
- verification: Production build browser smoke passed for `/stocks`, `/stocks/AAPL`, `/portfolio/coverage` at 375px, 768px, 1280px with zero horizontal overflow, `전일 대비` rendered on stock routes, and `평가손익률`/`평가손익` rendered on portfolio route.
- verification: Commit `65355c0e` was pushed to `develop`; EC2 `/opt/stockanalysis/app` fast-forwarded to `65355c0e`, `npm run typecheck`, `npm run build`, and service restart passed.
- verification: EC2 internal route smoke passed for `/`, `/stocks`, `/stocks/AAPL`, `/portfolio/coverage`, `/data-health`, and FastAPI `/__ready`.
- verification: Local tunnel `http://127.0.0.1:13000/stocks` rendered `전일 대비`; `http://127.0.0.1:13000/portfolio/coverage` rendered `평가손익률`.
- exact next step: Use the refreshed screens to decide the next visualization slice: portfolio return time-series chart, stock day-change heatmap, or collection/analysis coverage matrix.
