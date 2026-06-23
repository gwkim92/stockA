# tossinvest-shadow-daily-resource-guard-v1 Contract

## Task Request

- request: Understand and fix the EC2 instability caused by the TossInvest US shadow daily profile after the expanded US symbol universe was deployed.
- request: Keep TossInvest as read-only/shadow evidence, prevent large daily runs from overloading t3.small EC2, and make stale `running` pipeline rows visible in data-health.

## Objective
- Prevent TossInvest US shadow daily collection from overwhelming the EC2 instance.
- Make orphaned/stale `ops.pipeline_run` rows visible as stale instead of active running.
- Keep TossInvest as shadow evidence only. Do not promote it to canonical US pricing and do not change recommendation scoring.

## Goal

- goal: The scheduled TossInvest US shadow profile should run bounded daily slices (`outputsize=30`, max `10` symbols per run), trim any oversized candle payload before SQL upsert, and expose killed/orphaned `running` rows as `stale_running` in data-health.

## Scope
- Add defensive candle bar caps in the TossInvest market data runner.
- Add scheduled symbol batch limits for TossInvest US daily candles, provider comparison, and priority microdata.
- Update data-health SQL so old `running` rows are classified as stale.
- Add regression tests for symbol batching, candle trimming, operating profile command arguments, and data-health SQL.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/tossinvest_market_data.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_tossinvest_market_data.py`
  - `tests/test_operating_data_orchestrator.py`
  - `tests/test_data_operations_cadence.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/tossinvest-shadow-daily-resource-guard-v1/*`

## Out Of Scope
- No schema migration.
- No benchmark, recommendation weight, portfolio, broker, or order-flow changes.
- No systemd timer activation until EC2 smoke proves the reduced batch profile is stable.

## Verification Commands

- verification command: `python3 -m py_compile src/stockanalysis/operations/tossinvest_market_data.py src/stockanalysis/operations/cli.py src/stockanalysis/operations/operating_data_orchestrator.py src/stockanalysis/operations/cadence.py src/stockanalysis/frontend/live_adapter.py`
- verification command: `PYTHONPATH=src python3 -m unittest tests.test_tossinvest_market_data`
- verification command: `PYTHONPATH=src python3 -m unittest tests.test_operating_data_orchestrator tests.test_data_operations_cadence tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_data_health_sql_uses_operations_cadence_registry`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task tossinvest-shadow-daily-resource-guard-v1`
