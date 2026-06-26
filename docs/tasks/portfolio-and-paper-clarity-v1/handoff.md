# portfolio-and-paper-clarity-v1 Handoff

## Status

- implemented locally on `feature/professional-investment-ux-normalization-v1`.
- completed: portfolio and paper route decomposition is implemented locally and focused verification passed.

## Current Status

- Local implementation is complete for portfolio/paper decomposition.
- Local verification completed so far: `typecheck`, `npm test`, `npm run build`, `test:e2e`, `verify_frontend_api_contract`, `verify_project_execution_roadmap`, and AWH task verify.
- Browser QA screenshots were regenerated from production `next start` on `127.0.0.1:13003`.
- Merge to `develop` and EC2 rollout remain parent UX normalization rollout steps.

## Implemented

- Added `buildPortfolioCoverageViewModel` and `buildPaperTradingViewModel`.
- Portfolio coverage hero now foregrounds market value, unrealized profit/loss, return, and benchmark/feedback context instead of internal execution state.
- `PortfolioReturnSummaryPanel` table wrapper now has keyboard focus support for the scrollable region.
- Paper trading hero now separates simulated candidates from real orders and uses state wording:
  `실행 가능`, `안전장치 차단`, `데이터 부족`, `승인 필요`, `실거래 비활성`.
- Added `apps/web/src/app/paper-trading/PaperTradingPage.module.css` to stop the global command-grid card style from turning the first paper status card into an oversized blank block.
- Split `/portfolio/coverage` lower risk/rebalance/history sections into route-local components:
  - `apps/web/src/app/portfolio/coverage/_components/PortfolioCoverageDeepPanels.tsx`
  - `apps/web/src/app/portfolio/coverage/_components/PortfolioRiskBudgetPanels.tsx`
  - `apps/web/src/app/portfolio/coverage/_components/PortfolioDecisionFeedbackPanels.tsx`
  - `apps/web/src/app/portfolio/coverage/_components/PortfolioOutcomeCadencePanels.tsx`
  - `apps/web/src/app/portfolio/coverage/_components/PortfolioRebalancePanels.tsx`
  - `apps/web/src/app/portfolio/coverage/_components/PortfolioConcentrationPanels.tsx`
  - `apps/web/src/app/portfolio/coverage/_components/portfolioCoverageFormat.ts`
- Split `/paper-trading` lower state/action sections into route-local components:
  - `apps/web/src/app/paper-trading/_components/PaperCurrentStatePanel.tsx`
  - `apps/web/src/app/paper-trading/_components/PaperActionCandidatesSection.tsx`
  - `apps/web/src/app/paper-trading/_components/paperTradingFormat.ts`
- Added portfolio status copy mappings so `not available` and `wait` do not leak into investor-facing portfolio screens.
- Reduced route-file responsibility:
  - `/portfolio/coverage/page.tsx` now keeps data assembly, top decision cards, and section composition.
  - `/paper-trading/page.tsx` now keeps data assembly, hero copy, command cards, and section composition.
- Kept live broker submit blocked and did not change paper/order safety logic.

## Verification

- `cd apps/web && npm run typecheck`
- `cd apps/web && npm test`
- `cd apps/web && npm run build`
- `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13003 npm run test:e2e` (`54` passed)
- `bash scripts/verify_frontend_api_contract.sh`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task portfolio-and-paper-clarity-v1`
- Browser screenshot evidence:
  `/Users/woody/ai/stockanalysis/output/playwright/visual-quality-hard-gate-v1/portfolio-coverage-mobile-375.png`
  and `/Users/woody/ai/stockanalysis/output/playwright/visual-quality-hard-gate-v1/paper-trading-mobile-375.png`.

## Remaining

- `/data-health` remains the largest operations route. It already delegates overview/runtime/automation panels to `components/operations`, but default payloads, mapping helpers, and many detailed sections still live in the route file. That should be handled as a separate `operations-console-boundary-cleanup-v2` commit to avoid mixing investor page decomposition with operations-console internals.

## Exact Next Step

- Commit this focused decomposition, then continue the parent UX normalization sequence with operations console cleanup and final merge/deploy verification.
- exact next step: commit the portfolio and paper clarity slice, then continue `operations-console-boundary-cleanup-v2` without changing recommendation weights, DB schema, broker submit, or portfolio positions.
