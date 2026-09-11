#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
pg_bin="${STOCKA_TEST_POSTGRES_BIN:-$(pg_config --bindir)}"
task_pg_root=$(mktemp -d /tmp/stocka-financial-pg-XXXXXX)
task_pg_root=$(cd "$task_pg_root" && pwd -P)
cleanup() {
  "$pg_bin/pg_ctl" -D "$task_pg_root/data" -m fast stop >/dev/null 2>&1 || true
}
trap cleanup EXIT
mkdir "$task_pg_root/socket"
touch "$task_pg_root/disposable-financial-test"
"$pg_bin/initdb" -D "$task_pg_root/data" -A trust --no-locale > "$task_pg_root/initdb.log"
"$pg_bin/pg_ctl" -D "$task_pg_root/data" -l "$task_pg_root/postgres.log" -o "-k $task_pg_root/socket -p 55491 -h ''" start
"$pg_bin/createdb" -h "$task_pg_root/socket" -p 55491 stocka_financial_test
export STOCKA_FINANCIAL_TEST_SOCKET="$task_pg_root/socket"
export STOCKA_FINANCIAL_TEST_PSQL="$pg_bin/psql"
export PYTHONPATH=src
python3 -m unittest tests.test_sec_companyfacts tests.test_financial_period_integrity \
  tests.test_financial_period_integrity_postgres tests.test_professional_equity_analysis \
  tests.test_professional_coverage_expansion -v
