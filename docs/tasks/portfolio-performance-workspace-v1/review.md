# Holdings and performance workspace — review

## Product scope

The primary pages now focus on recorded holdings, missing research evidence, review reasons and measured recommendation outcomes. Search/filter and report dates are functional, not decorative. Existing backend financial calculations, benchmarks, evaluation criteria, portfolio state and order permissions are unchanged.

The old portfolio page is preserved verbatim as `LegacyPortfolioPage.tsx` (original blob `89090a86a62bac8091c90ab10e0dbbe8d39ff573`) and deliberately opened at `/portfolio/coverage/details`. Its latest-policy behavior is explicitly distinguished from selected-date primary reports. Both legacy links disable automatic prefetch; this is tested using the actual `/api/trading/readiness` endpoint, not a similar-looking route.

## Evidence and numerical presentation

- Exact portfolio identity and primary row IDs are validated; empty successful lists are different from failed/invalid payloads.
- Only explicit same-base-currency, nonnegative market-value and positive-cost rows contribute to the shown subtotal. Native-currency values are not substituted. Exclusion counts stay visible.
- Existing presentation return helpers are reused. Subtotals are not called full account balances, strategy backtests or cash-flow-adjusted returns.
- Whole-report averages/hit rates are not recalculated from filtered rows. No samples means unmeasured, not an invented 100 percent hit rate.
- Percent returns, percentage-point alpha and basis-point attribution have separate units. Overlapping attribution lenses are not summed.
- Feedback joins the exact stored history reference and portfolio; latest review records are not described as prior/current changes.
- Requested dates are sent to the backend; invalid/future/duplicate dates stop before IO. Response dates remain visible and are not overwritten by the requested date.

## Accessibility and navigation

Summary definition lists now use valid dt/dd grouping. The chosen date is preserved between holdings and performance tabs. Failed reads keep navigation and do not expose raw error payloads. The primary holdings route has no dependency on trading readiness; deliberate legacy navigation still renders that existing detail path.

Actual mobile browser captures showed excessive explanatory text ahead of the first record. Repeated copy moved after results or into a standard disclosure; measurement counts, exclusion counts, dates and order-disabled context remain visible. A four-column compact summary is used only for short outcome numbers, not currency amounts. No CSS is injected or interface elements hidden for screenshots.

## Verification interpretation

Full frontend tests, production build/typecheck and browser checks run on clean GitHub runners using isolated synthetic API fixtures, not live investment data. The first integration fixture incorrectly used `/api/trading-readiness`; the fixture and assertions were corrected to the actual adapter path `/api/trading/readiness`. The production endpoint was not changed. Later mobile first-record assertions failed; the UI was corrected without relaxing the assertions.

No independent reviewer approval, current EC2 health, actual market-data accuracy, whole-backend regression, investment profitability or production deployment is claimed. The final head's workflow and PR merge state are required before integration.
