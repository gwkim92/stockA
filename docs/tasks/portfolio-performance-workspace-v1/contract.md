# Portfolio and performance workspace v1

Continue the user's overall UX/UI overhaul after PR #30. Base develop@9b1717d13989a2c584aa8aafbb1b3bb01887880b. Prioritize actual investor review over more readiness/audit wrappers.

## Scope

Redesign `/portfolio/coverage` and `/performance` around holdings, gaps in investment theses, recorded review decisions, and measured recommendation outcomes. Keep source dates and read-only boundaries explicit. Search/filter/date selection should persist in the URL. Do not call mark-to-market P&L a strategy backtest; do not sum overlapping attribution lenses or combine native currencies as base-currency totals. Keep missing values different from zero and empty lists different from request failures.

Use existing stored data and existing position-return calculations, with explicit same-base and complete-value eligibility for presented subtotals. No change to backend computations. The legacy portfolio policy/feedback panels remain reachable at `/portfolio/coverage/details` rather than preceding the primary holdings workflow. Preserve old source/benchmark/evaluation definitions. The primary holdings page must not depend on the trading-readiness endpoint.

Report average alpha/hit rate are whole-report values, not recomputed by local list filters. Alpha is a return difference in percentage points; contribution basis points have their own unit. Per-row horizon is separate from the shared report measurement window. Latest recorded decisions are not falsely presented as a prior/current change comparison; feedback may only join the exact referenced history artifact.

## Acceptance and boundaries

Add contract/model/transport tests, production-browser desktop/mobile tests for filters, date requests, partial/missing currencies, zero/unknown outcomes, recorded-history mismatches, error recovery, accessible controls and no page-width overflow. Run existing 194 unit / 64 browser regression plus new cases, production build/typecheck and blocking dependency audits. Inspect actual browser captures before integration.

Do not modify main, backend/schema, financial scoring/weight/benchmarks/evaluation splits, orders, broker, portfolio state, production secrets, AWS or deployments. Actual EC2 records are not available in this execution session; record this limitation, do not create a substitute DB. Changes and tests use the connected GitHub tools/clean CI runner. No independent reviewer approval is implied.
