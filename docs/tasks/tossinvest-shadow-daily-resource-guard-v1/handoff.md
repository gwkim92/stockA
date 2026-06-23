# tossinvest-shadow-daily-resource-guard-v1 Handoff

## Current Status
- status: implemented_local_changes_focused_verification_passed_ec2_smoke_pending
- in progress: local resource guard implementation is complete; EC2 reduced-batch smoke and timer activation remain pending.
- current status: Implemented local code changes and focused verification passed. EC2 timer activation remains blocked until reduced-batch smoke passes after instance access is stable.

## Root Cause
- `toss-candles-us-shadow-daily` used the expanded Toss US symbol universe in one run.
- The TossInvest runner trusted provider candle payload size and stored raw candle payload as repeated row evidence.
- If a process was killed, `ops.pipeline_run` could remain `running`; data-health showed it as active instead of stale.

## Changes
- Added TossInvest scheduled defaults:
  - daily candle output size: `30`
  - scheduled max symbols per run: `10`
- Added `--max-symbols-per-run` to:
  - `tossinvest-market-data-sync-run`
  - `tossinvest-provider-comparison-run`
- Added date-rotated symbol batching so daily jobs process a bounded slice instead of the full universe.
- Added candle outputsize validation and latest-N bar trimming before DB upsert.
- Replaced full raw candle payload evidence with compact evidence for candle rows.
- Updated operating profile commands:
  - `toss-candles-us-shadow-daily` now passes `--outputsize 30 --max-symbols-per-run 10`
  - `toss-provider-comparison-daily` now passes `--max-symbols-per-run 10`
  - `toss-priority-microdata-intraday` now passes `--max-symbols-per-run 10`
- Updated cadence command templates to match the reduced operational profile.
- Updated data-health SQL so stale `started/running` rows become `stale_running` and trigger attention.

## Verification
- `python3 -m py_compile src/stockanalysis/operations/tossinvest_market_data.py src/stockanalysis/operations/cli.py src/stockanalysis/operations/operating_data_orchestrator.py src/stockanalysis/operations/cadence.py src/stockanalysis/frontend/live_adapter.py`
- `PYTHONPATH=src python3 -m unittest tests.test_tossinvest_market_data`
- `PYTHONPATH=src python3 -m unittest tests.test_operating_data_orchestrator tests.test_data_operations_cadence tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_data_health_sql_uses_operations_cadence_registry`
- `PYTHONPATH=src python3 -m unittest tests.test_tossinvest_market_data tests.test_operating_data_orchestrator tests.test_data_operations_cadence tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_data_health_sql_uses_operations_cadence_registry`
- `git diff --check`

## Known Residuals
- `PYTHONPATH=src python3 -m unittest tests.test_data_operations_cli` still has an unrelated local failure in `test_manual_host_scheduler_activation_preflight_command_writes_output`, returning `blocked_runtime_env_not_ready`.
- Existing EC2 stale row such as `pipeline-run-7077` is not mutated by frontend code. It should now be surfaced as `stale_running`; direct cleanup can be done after SSH recovers.
- Systemd timer should not be installed until EC2 smoke verifies the reduced Toss profile no longer harms sshd responsiveness.

## Exact Next Step
- exact next step: Restore EC2 SSH access if still timed out, deploy this change from `develop`, then run `stockanalysis-operations operating-data-run --profile toss-candles-us-shadow-daily --execute` once and confirm selected symbol count `10`, candle bar count near `10 * 30`, `failed_step_count=0`, and SSH remains responsive before enabling timers.

## Next EC2 Steps
- Restore SSH access if still timed out.
- Pull this commit on EC2 from `develop`.
- Run `stockanalysis-operations operating-data-run --profile toss-candles-us-shadow-daily --execute` once and confirm selected symbol count `10`, candle bar count is bounded near `10 * 30`, `failed_step_count=0`, and SSH remains responsive during and after the run.
- Only after that, install/enable the Toss timers.
