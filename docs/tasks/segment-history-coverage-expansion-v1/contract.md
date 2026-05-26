# segment-history-coverage-expansion-v1 Contract

## Purpose

Expand trend-backed reported segment history from the AAPL proof to active recommendation and portfolio coverage, while reporting unsupported issuer/table layouts instead of hiding them behind single-period proxy assumptions.

## Scope

- Use existing `stockanalysis-operations` backend CLI/service boundaries.
- Run bounded historical reported segment backfill for active recommendation and portfolio symbols with known SEC CIK coverage.
- Record coverage counts by symbol: periods parsed, segment labels parsed, unsupported candidate count, single-period fallback count, and bad-label count.
- Keep recommendation scoring weights, benchmark rules, portfolio guardrails, and broker/order flow unchanged.
- Prefer deterministic parser coverage and explicit quality reporting before adding AI extraction for financial tables.

## Non-Goals

- No recommendation weight changes.
- No live broker submit.
- No paid external financial data provider.
- No unbounded SEC archive crawling.

## Acceptance Criteria

- A backend runner or existing runner profile can process a bounded active-symbol set and produce a coverage report.
- Unsupported layouts are surfaced as quality gaps, not silent success.
- AAPL remains clean: 4 annual periods, 5 segment labels, bad segment count `0`, trend-backed SOTP assumptions.
- At least one non-AAPL active symbol is attempted and its result is reported as parsed or unsupported.
- Task handoff records EC2 run IDs and API/DB evidence.
