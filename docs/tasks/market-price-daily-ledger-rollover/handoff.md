# Session Handoff

## Active Task

- 이름: market-price-daily-ledger-rollover
- 담당: Codex
- 날짜: 2026-05-19

## Current Status

- 완료:
  - task contract and plan created.
  - before live `/api/data-health` captured provider budget `day_missing` for `2026-05-19`, market freshness `2026-05-15`, and overall status `healthy`.
  - repo-outside runtime env readiness passed for database, FRED, Twelve Data provider, SEC identity, portfolio snapshot source, Codex OAuth LLM provider, market price history, and artifact root.
  - scheduler-free market-price daily run succeeded through `stockanalysis-operations run`.
  - artifact: `/private/tmp/stockanalysis-runtime/artifacts/20260519T010224Z_market-price-daily`.
  - command used `budget-date=2026-05-19` and `freshness-date=2026-05-18`.
  - Twelve Data result: requested 20 symbols, provider requests 20, succeeded 20, skipped 0, failed 0, total bars 2000, remaining budget 780 of 800.
  - DB sample confirmed all 20 expanded watchlist symbols have latest `market.daily_price_bar.trade_date=2026-05-18` and 101 bars each.
  - after live `/api/data-health` captured provider budget `configured`, used `20`, remaining `780`, latest market run `pipeline-run-89`, market freshness `2026-05-18`, and overall status `healthy`.
  - `/data-health` UI was refreshed in Chrome and shows `호출 예산 780 / 800`, `pipeline-run-89`, and `market.daily price bar observed · 2026-05-18`.
  - UI wrap issue found during browser verification was fixed by adding `rail-ratio-value` styling for the provider budget ratio.
  - frontend typecheck/build passed.
- 진행 중:
  - final AWH/diff verification.
- 막힌 점:
  - none yet.

## Exact Next Step

- exact next step: trading-day freshness target policy was implemented in `market-price-latest-completed-day-policy`; continue with scheduler manual/pending hardening or real portfolio source integration.

## Verification

- Passed:
  - before authorized `/api/data-health` query showed provider budget `day_missing` for `2026-05-19`.
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m stockanalysis.operations.cli env-readiness --env-file /private/tmp/stockanalysis-runtime/data-operations.real.env`
  - market-price daily artifact run succeeded: `/private/tmp/stockanalysis-runtime/artifacts/20260519T010224Z_market-price-daily/stdout.json`.
  - after authorized `/api/data-health` query showed provider budget `configured`, `20` used, `780` remaining, and market freshness `2026-05-18`.
  - local Postgres sample confirmed all 20 expanded watchlist symbols latest date `2026-05-18`.
  - Chrome UI smoke confirmed `/data-health` renders `호출 예산 780 / 800`, `pipeline-run-89`, and `market.daily price bar observed · 2026-05-18`.
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
- Pending:
  - AWH task verification
  - `git diff --check`

## Risks

- This run consumed 20 real Twelve Data free-tier calls for 2026-05-19 local budget accounting.
- The command required a manual `--freshness-date 2026-05-18` in this task. The follow-up `market-price-latest-completed-day-policy` task implemented automatic latest completed market date resolution.
- The current DB boundary still uses the Docker-backed legacy `STOCKANALYSIS_PSQL_COMMAND`, so execution may require elevated Docker access.
