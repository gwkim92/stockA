# visual-quality-hard-gate-v1 Handoff

## Status

- implemented as a local verification gate for the UX normalization slice.
- status: implemented locally on `feature/professional-investment-ux-normalization-v1`.
- completed: local e2e hard gate, production screenshot capture, and forbidden-copy checks are implemented for this UX slice.

## Current Status

- current status: local hard gate is implemented and verified against production `next start` on `127.0.0.1:13003`.
- current status: e2e forbidden-copy scan now covers investor routes, detail routes, live recommendation detail, portfolio, paper trading, and operations routes.
- current status: screenshot evidence has been regenerated under `output/playwright/visual-quality-hard-gate-v1/`.

## Implemented

- Existing Playwright professional workspace e2e suite was run against production `next start` at `http://127.0.0.1:13003`.
- Verified responsive routes at mobile/tablet/desktop through e2e:
  `/`, `/market-map`, `/cycle-map`, `/intelligence`, `/stocks`, `/recommendations`, `/portfolio/coverage`, `/paper-trading`,
  `/stocks/AAPL`, `/recommendations/AAPL-2024-11-01`, `/ai-evidence/sec-event-aapl-10k-20240928`,
  `/data-health`, `/admin/ai-agents`, `/trading-readiness`, `/remediation`.
- Captured screenshots for key changed screens at `375x900`, `768x1000`, and `1280x900`.
- Direct visual QA found an oversized paper-trading hero caused by global command-grid styles; fixed with a route-local CSS Module and recaptured screenshots.
- Direct visual QA found excessive fallback recommendation hero whitespace on the local fixture route; fixed with compact compatibility styling and recaptured screenshots.
- Direct visual QA found `/stocks/AAPL` showing raw provider state as `분석 기준 가격 · missing`; fixed provider-label mapping and recaptured screenshots.
- Direct visual QA found `/portfolio/coverage` showing raw English states `not available` and `wait`; fixed portfolio copy mappings and expanded the forbidden-copy e2e gate.
- Added fixture API alias coverage so recommendation list id `recommendation-7101` resolves to the existing AAPL detail fixture during local e2e.
- Re-ran Playwright after the copy cleanup and provider-label fix.

## Evidence

- `cd apps/web && npm run typecheck`
- `cd apps/web && npm test` (`14` files, `36` tests)
- `cd apps/web && npm run build`
- `PYTHONPATH=src python3 -m unittest tests.test_frontend_api_adapter tests.test_frontend_fixture_server -v` (`40` tests)
- `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13003 npm run test:e2e` (`54` passed)
- Screenshot directory:
  `/Users/woody/ai/stockanalysis/output/playwright/visual-quality-hard-gate-v1`
- Latest focused screenshots include:
  `recommendation-live-mobile-375.png`, `recommendation-live-desktop-1280.png`,
  `stock-aapl-mobile-375.png`, `stock-aapl-desktop-1280.png`,
  `portfolio-coverage-mobile-375.png`, `paper-trading-mobile-375.png`.

## Remaining

- This is not a full design-system rewrite. It validates the first slice and records visible screenshots.
- Lighthouse/react-scan deep performance gates were not run in this slice; run them after the major page files are further decomposed.

## Exact Next Step

- exact next step: commit the visual hard gate updates with the related UX copy fixes, then continue `operations-console-boundary-cleanup-v2` and run the same e2e/screenshot gate after that route is decomposed.
