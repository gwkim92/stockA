# tossinvest-shadow-daily-resource-guard-v1 Handoff

## Current Status
- status: completed_ec2_reduced_batch_smoke_passed_timer_activation_still_not_enabled
- completed: Local resource guard implementation, GitHub push, EC2 deploy, reduced-batch Toss profile smoke, stale run cleanup, and route smoke are complete.
- current status: Reduced TossInvest US shadow daily profile is deployed to EC2 and verified. Toss-specific systemd timers remain not installed/enabled, by design.

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
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task tossinvest-shadow-daily-resource-guard-v1`
- EC2 deploy: `/opt/stockanalysis/app` fast-forwarded from `a70b0361` to `b10945ac`.
- EC2 reduced Toss smoke: `operating-data-run --profile toss-candles-us-shadow-daily --execute` returned `run_status=completed`, `failed_step_count=0`.
- EC2 Toss candle step: `run_id=7079`, requested `46`, selected `10`, `outputsize=30`, `candle_bar_count=300`, selected symbols `TLT/TSLA/XLB/XLC/XLE/XLF/XLI/XLK/XLP/XLRE`.
- EC2 Toss comparison step: `run_id=7080`, requested `46`, selected `10`, `comparison_count=10`, `shadow_collecting_count=10`.
- EC2 stale cleanup: `pipeline-run-7077` was `running` with `ended_at=null`; marked `failed` with orphaned cleanup reason after rerun succeeded.
- EC2 route smoke: `http://127.0.0.1:3000/`, `http://127.0.0.1:13000/`, and `http://127.0.0.1:8787/__ready` returned `200`.

## Known Residuals
- `PYTHONPATH=src python3 -m unittest tests.test_data_operations_cli` still has an unrelated local failure in `test_manual_host_scheduler_activation_preflight_command_writes_output`, returning `blocked_runtime_env_not_ready`.
- Data-health expected jobs still collapse several Toss market-data jobs by shared `pipeline_name=tossinvest_market_data_sync`; latest Toss market-data run may display under a generic/neighbor Toss job label. This is visibility debt, not the resource-exhaustion root cause.
- Toss-specific systemd timers were not installed/enabled. Reduced profile smoke passed, but timer activation should be a separate explicit operations step.

## Exact Next Step
- exact next step: Fix Toss data-health job label granularity by recording or deriving step/job identity for shared `tossinvest_market_data_sync` runs, then decide whether to install Toss-specific timers after another small-batch smoke window.

## Next EC2 Steps
- Keep monitoring SSH responsiveness and load after the reduced profile.
- Do not run full Toss US universe backfill on the daily profile.
- If backfill is needed, implement a separate manual chunked backfill profile with explicit batch/window controls.
