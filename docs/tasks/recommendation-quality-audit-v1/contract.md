# Recommendation Quality Audit v1

Base: develop@db933728934078f8de099685883fbc9a5bd3cdd7 (PR #46 merged and post-merge verified).

## Goal

Move stockA from displaying recommendation outcomes to auditing whether the stored performance report is internally coherent and where the decision process appears strong, weak or unmeasured. The first release is a read-only evaluation layer on the existing performance-outcomes API. It does not change recommendation scores, generate trades or rewrite historical outcomes.

## Delivered questions

- How many received outcomes are actually measurable (finite alpha + positive horizon), and how many remain unmeasured?
- Do stored summary values agree with the received outcome rows for measured count, average alpha and hit rate?
- How do measured outcomes break down by observation horizon and recommendation action?
- What proportion of measured outcomes retain recommendation/thesis links?
- Which coverage exclusions and quality gates remain in the report?
- Which attribution lenses are present, without falsely adding explanatory lenses into total P&L?

## Rules

Use only the already returned report. Never fabricate missing rows, dates, benchmark results, recommendation links or thesis links. A derived row statistic must be labeled as derived from received rows. A stored report statistic must remain labeled as stored/report-level. Differences between them are an audit finding, not an automatic correction.

Do not introduce arbitrary investment-performance pass/fail thresholds. Preserve the producer-provided quality_evaluation status/sample_size_status verbatim through existing safe text helpers. Cohorts with zero measurable rows show unknown/unmeasured, never 0% hit rate or 0 alpha. Different horizons are separate cohorts and are not combined into an annualized strategy return.

Attribution components are explanatory lenses. Security selection, theme exposure and cash timing are shown separately and never summed into total return. Coverage exclusions remain separate from measured outcomes. Unknown/malformed structures degrade to explicit unavailable states.

## Scope

Frontend model + performance workspace presentation + synthetic fixture/test coverage only for v1. No backend/SQL/schema/migrations/seeds, recommendation weights, scoring rules, benchmark/evaluation golden data, portfolio/order/broker writes, dependency/lockfile, workflow, secrets/AWS, scheduler, main or deployment changes.

A later phase may persist evaluation runs and recommendation-version snapshots after this read-only audit contract is verified. This PR must not pretend that persistence already exists.

## Verification

Add pure model tests for measured eligibility, derived statistics, summary mismatch detection, horizon/action cohorts, missing linkage, exclusions/gates and malformed values. Extend the existing production-browser performance tests on desktop/mobile without weakening current assertions. Run the unchanged Web Product Quality workflow, inspect actual final performance screenshots, and record observed counts/results before integration.
