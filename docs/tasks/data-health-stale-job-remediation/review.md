# Data Health Stale Job Remediation Review

## Verification

- Before live API state:
  - authorized `GET /api/data-health` returned `overall_status=attention_required`.
  - stale: `portfolio-position-daily`, `portfolio-remediation-daily`.
  - missing: `performance-outcome-monthly`.
- Corrected local runtime input:
  - `/private/tmp/stockanalysis-runtime/positions.local-fixture.csv` was updated outside the repo to include required `market_price` and `market_value` columns.
  - AAPL price came from canonical `market.daily_price_bar`: latest `trade_date=2026-05-15`, `close=300.230010`.
- Artifact runner results:
  - `portfolio-position-daily`: succeeded, artifact `/private/tmp/stockanalysis-runtime/artifacts/20260519T001357Z_portfolio-position-daily`, run_id `61`, one AAPL position for snapshot `2026-05-18`.
  - `portfolio-remediation-daily`: succeeded, artifact `/private/tmp/stockanalysis-runtime/artifacts/20260519T001436Z_portfolio-remediation-daily`, run_id `62`, three open tickets in the final report.
  - `performance-outcome-monthly`: succeeded, artifact `/private/tmp/stockanalysis-runtime/artifacts/20260519T001453Z_performance-outcome-monthly`, run_id `65`, four due horizons succeeded.
- After live API state:
  - authorized `GET /api/data-health` returned `overall_status=healthy`.
  - affected jobs `portfolio-position-daily`, `portfolio-remediation-daily`, and `performance-outcome-monthly` all returned `health_status=ok`.
  - `portfolio.position_snapshot` freshness moved to latest observation date `2026-05-18`.
- Frontend state:
  - Next.js dev server had stopped and was restarted at `http://127.0.0.1:3001`.
  - Chrome UI smoke confirmed `/data-health` renders Korean status `정상`, failure count `0`, `수동 승인 대기`, and the updated pipeline run ids `pipeline-run-61`, `pipeline-run-62`, and `pipeline-run-65`.
- Scheduler boundary:
  - no `launchctl` command was executed.
  - no host LaunchAgents file was written.
  - activation remains `pending_manual_approval`.
- Harness and diff:
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task data-health-stale-job-remediation`
  - `git diff --check`

## Residual Risks

- The initial stale cause included a bad local positions fixture. This is fixed for local MVP, but a real portfolio source/export format is still needed before production-like operation.
- Provider budget now shows `day_missing` for `2026-05-19` because the budget day rolled forward and no market-price job has recorded a ledger entry for that date yet.
- The local DB still mixes real-provider data with bootstrap fixture signal/recommendation data, so healthy operations status does not mean investment recommendation quality is production-ready.
