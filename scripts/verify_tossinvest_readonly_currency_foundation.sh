#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-}"

if [ -z "$PYTHON_BIN" ]; then
  if [ -x /opt/homebrew/bin/python3.13 ]; then
    PYTHON_BIN="/opt/homebrew/bin/python3.13"
  else
    PYTHON_BIN="python3"
  fi
fi

cd "$ROOT_DIR"

echo "Verifying TossInvest read-only source, sync, CLI, and order boundary"
PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_tossinvest_source \
  tests.test_tossinvest_readonly_sync \
  tests.test_tossinvest_order_adapter \
  tests.test_data_operations_cli.DataOperationsCliTests.test_tossinvest_readonly_sync_run_dry_run_is_secret_free \
  tests.test_data_operations_cli.DataOperationsCliTests.test_tossinvest_readonly_sync_run_rejects_repo_inside_env_file

echo "Verifying frontend read model visibility"
PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_trading_readiness_response_matches_frontend_contract_shape \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_trading_readiness_sql_reads_safety_tables_without_exposing_secrets \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_portfolio_coverage_response_matches_frontend_contract_shape \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_data_health_sql_uses_operations_cadence_registry \
  tests.test_portfolio_outcome_coverage_report

echo "Checking migration and seed references"
rg -q "create table if not exists market\\.fx_rate_snapshot" db/migrations/0033_tossinvest_currency_foundation.sql
rg -q "native_currency_code" db/migrations/0033_tossinvest_currency_foundation.sql
rg -q "'KR', 'Korea Equities', 'KR', 'KRW', 'Asia/Seoul'" db/seeds/0001_reference_seed.sql
rg -q "'KR', 'XKRX', 'Korea Exchange', 'Asia/Seoul'" db/seeds/0001_reference_seed.sql

echo "TossInvest read-only currency foundation verification passed"
