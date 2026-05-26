# segment-history-coverage-expansion-v1 Handoff

## Status

- pending: start after `segment-history-backfill-v1` closes.

## Context

- `segment-history-backfill-v1` proved the path on AAPL and fixed parser pollution from total/tax tables.
- Current EC2 proof: AAPL has 4 annual reported segment periods, 5 clean geographic segment labels per period, `bad_segment_count=0`, and SOTP assumptions use `multi_period_segment_trend_template`.

## Exact Next Step

- Design and implement a bounded active-symbol segment history coverage runner/report using existing backend CLI/service boundaries.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not add shell-only orchestration when a backend CLI/service boundary is appropriate.
