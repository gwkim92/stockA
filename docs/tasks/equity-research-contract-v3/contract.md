# Equity research contract v3

User request: continue stockA carefully after PR #36. Base develop@9c90f5f7220861a2f57d4ee7e5e5dd72d588fa83.

## Objective

Close the still-open equity reporting defects using direct changes to its existing runtime, reproducible regressions and exact tested-commit evidence. No claim of being production-complete or the best project follows from unit tests.

## Scope

Inspect equity_research_reporting.py and its caller/test contracts. Preserve explicit confidence zero; reject non-finite, boolean, string or out-of-range model numbers instead of coercing/clamping them. Validate the existing research output schema at parsing and before accepting injected provider results. Frame supplied source data, enforce a final intact source-character budget, and remove minimum-claim pressure for weak evidence. Keep prompt/version/request-hash relationships and the data actually supplied to the provider consistent. Preserve the existing SQL/storage schema, model selection and deterministic financial rules.

Add tests that fail against baseline and cover valid outputs as well as rejection, no real model/DB calls, wrong-value no-successful-write paths, input bounds and preserved source records. Run the current selected prompt regressions on Python 3.11 and 3.13 before develop integration. Do not change golden cases/thresholds to make tests pass.

## Execution and boundaries

The prior broader equity upload was denied; this task makes a normal authorized, explicitly scoped repository update. If that action is denied again, do not encode, relocate or apply the change through an alternate write route. Report the actual state. The existing tracked source archive may be used for offline processing only after matching affected file blobs with the current base; it is not a complete current checkout. No new export workflow is needed.

No main, actual database or replacement database, migration/seed/schema, scoring weights, benchmark/evaluation split, portfolio/order/broker, accounts/secrets/AWS, scheduler, dependency/lockfile or deployment changes. Paid generation, live model quality, semantic entailment, current workload rejection rates and operating EC2 data remain outside this offline task. Keep final findings and verification in this directory and on the PR.