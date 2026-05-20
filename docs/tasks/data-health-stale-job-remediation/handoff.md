# Session Handoff

## Active Task

- 이름: data-health-stale-job-remediation
- 담당: Codex
- 날짜: 2026-05-19

## Current Status

- 완료:
  - task contract and plan created.
  - before state captured from live `/api/data-health`: overall `attention_required`, stale `portfolio-position-daily`, stale `portfolio-remediation-daily`, and missing `performance-outcome-monthly`.
  - first `portfolio-position-daily` run failed because `/private/tmp/stockanalysis-runtime/positions.local-fixture.csv` only had `symbol,quantity` and missed required `market_price` and `market_value` columns.
  - repo-outside positions fixture was repaired with canonical AAPL latest close `300.230010` from `market.daily_price_bar` through `2026-05-15`.
  - `portfolio-position-daily` succeeded through `stockanalysis-operations run`, artifact `/private/tmp/stockanalysis-runtime/artifacts/20260519T001357Z_portfolio-position-daily`, run_id `61`, snapshot date `2026-05-18`, one AAPL paper position linked to one thesis.
  - `portfolio-remediation-daily` succeeded through `stockanalysis-operations run`, artifact `/private/tmp/stockanalysis-runtime/artifacts/20260519T001436Z_portfolio-remediation-daily`, run_id `62`, review run_id `63`, ticket bootstrap run_id `64`, three open remediation tickets.
  - `performance-outcome-monthly` succeeded through `stockanalysis-operations run`, artifact `/private/tmp/stockanalysis-runtime/artifacts/20260519T001453Z_performance-outcome-monthly`, run_id `65`, four due horizons succeeded and produced four recommendation outcomes plus four thesis outcomes.
  - after state captured from live `/api/data-health`: overall `healthy`, `portfolio-position-daily`, `portfolio-remediation-daily`, and `performance-outcome-monthly` all `ok`.
  - freshness now reports `portfolio.position_snapshot` latest observation date `2026-05-18`.
  - scheduler activation remains pending manual approval and no host scheduler mutation was performed.
  - provider budget status rolled to `day_missing` for budget date `2026-05-19`; this does not currently affect overall health and means no Twelve Data run has been recorded for the new budget day.
  - Next.js dev server on `127.0.0.1:3001` had stopped and was restarted for UI verification.
  - Chrome UI smoke confirmed `/data-health` renders `정상`, `실패 파이프라인 0`, `수동 승인 대기`, and current pipeline rows with `ok` health.
  - task review updated.
  - broader local-live handoff/review updated.
  - AWH task verification passed.
  - `git diff --check` passed.
- 진행 중:
  - none.
- 막힌 점:
  - none.

## Exact Next Step

- exact next step: decide whether to keep scheduler activation manual/pending and move to real portfolio source/provider freshness policy, or prepare a real `market-price-daily` approval packet for external manual operator review.

## Verification

- Passed:
  - before authorized `/api/data-health` query showed `attention_required` with two stale daily portfolio jobs and one missing monthly performance job.
  - `portfolio-position-daily` artifact run succeeded: `/private/tmp/stockanalysis-runtime/artifacts/20260519T001357Z_portfolio-position-daily/stdout.json`.
  - `portfolio-remediation-daily` artifact run succeeded: `/private/tmp/stockanalysis-runtime/artifacts/20260519T001436Z_portfolio-remediation-daily/stdout.json`.
  - `performance-outcome-monthly` artifact run succeeded: `/private/tmp/stockanalysis-runtime/artifacts/20260519T001453Z_performance-outcome-monthly/stdout.json`.
  - after authorized `/api/data-health` query showed overall `healthy` and all affected jobs `ok`.
  - Chrome UI smoke for `http://127.0.0.1:3001/data-health` showed Korean page status `정상`, failure count `0`, and updated runs `pipeline-run-61`, `pipeline-run-62`, `pipeline-run-65`.
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task data-health-stale-job-remediation`
  - `git diff --check`
- Pending:
  - none.

## Risks

- The current DB boundary still uses the legacy Docker-backed `STOCKANALYSIS_PSQL_COMMAND`, so local command execution may require explicit elevated Docker access.
- `performance-outcome-monthly` succeeded in this run, but it used currently available bootstrap candidates and does not prove full production outcome coverage.
- Provider budget status is `day_missing` for `2026-05-19` until the next market-price daily run records a ledger entry for the new day.
