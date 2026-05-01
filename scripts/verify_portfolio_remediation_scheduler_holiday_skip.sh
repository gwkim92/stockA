#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
ARTIFACT_ROOT=$(mktemp -d /tmp/stockanalysis-scheduler-holiday-skip.XXXXXX)
OUTPUT_PATH_FILE="$ARTIFACT_ROOT/skip-output-path.txt"

cleanup() {
  rm -rf "$ARTIFACT_ROOT"
}

trap cleanup EXIT

cd "$ROOT_DIR"

bash -n scripts/run_portfolio_remediation_daily_scheduler.sh
bash -n scripts/verify_portfolio_remediation_scheduler_holiday_skip.sh

STOCKANALYSIS_PSQL_COMMAND="psql postgresql://example.invalid/stockanalysis" \
PORTFOLIO_REMEDIATION_AS_OF_DATE="2024-11-01" \
PORTFOLIO_REMEDIATION_UNIVERSE_VERSION="fixture-v1" \
PORTFOLIO_REMEDIATION_COVERAGE_MEASUREMENT_END_DATE="2024-12-02" \
PORTFOLIO_REMEDIATION_TICKET_LIMIT="5" \
PORTFOLIO_REMEDIATION_ARTIFACT_ROOT="$ARTIFACT_ROOT" \
PORTFOLIO_REMEDIATION_RUN_DATE="2026-01-01" \
PORTFOLIO_REMEDIATION_SKIP_DATES="2025-12-25,2026-01-01 2026-01-19" \
PORTFOLIO_REMEDIATION_SKIP_REASON="nyse_holiday" \
scripts/run_portfolio_remediation_daily_scheduler.sh > "$OUTPUT_PATH_FILE"

JSON_PATH=$(cat "$OUTPUT_PATH_FILE")
STDERR_PATH="${JSON_PATH%.json}.stderr.log"

python3 - "$JSON_PATH" "$STDERR_PATH" "$ARTIFACT_ROOT" <<'PY'
import json
import os
import sys

json_path, stderr_path, artifact_root = sys.argv[1:]

assert json_path.startswith(artifact_root + os.sep), json_path
assert os.path.isfile(json_path), json_path
assert os.path.isfile(stderr_path), stderr_path

with open(json_path, "r", encoding="utf-8") as handle:
    payload = json.load(handle)

assert payload["report_name"] == "portfolio_remediation_scheduler_skip", payload
assert payload["status"] == "skipped", payload
assert payload["skip_type"] == "configured_skip_date", payload
assert payload["skip_reason"] == "nyse_holiday", payload
assert payload["run_date"] == "2026-01-01", payload
assert payload["as_of_date"] == "2024-11-01", payload
assert payload["portfolio_name"] == "Long Term Paper", payload
assert payload["strategy_name"] == "long_term_core", payload
assert payload["horizon_type"] == "long_term", payload
assert payload["universe_version"] == "fixture-v1", payload
assert payload["coverage_measurement_end_date"] == "2024-12-02", payload
assert payload["skip_dates"] == ["2025-12-25", "2026-01-01", "2026-01-19"], payload

with open(stderr_path, "r", encoding="utf-8") as handle:
    stderr = handle.read()
assert "scheduler skipped for run_date=2026-01-01" in stderr, stderr
PY

STOCKANALYSIS_PSQL_COMMAND="psql postgresql://example.invalid/stockanalysis" \
PORTFOLIO_REMEDIATION_AS_OF_DATE="2024-11-01" \
PORTFOLIO_REMEDIATION_UNIVERSE_VERSION="fixture-v1" \
PORTFOLIO_REMEDIATION_COVERAGE_MEASUREMENT_END_DATE="2024-12-02" \
PORTFOLIO_REMEDIATION_ARTIFACT_ROOT="$ARTIFACT_ROOT/preflight" \
PORTFOLIO_REMEDIATION_RUN_DATE="2026-01-02" \
PORTFOLIO_REMEDIATION_SKIP_DATES="2026-01-01" \
scripts/run_portfolio_remediation_daily_scheduler.sh --preflight-only > "$ARTIFACT_ROOT/preflight.json"

python3 - "$ARTIFACT_ROOT/preflight.json" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    payload = json.load(handle)

assert payload["preflight"] == "passed", payload
assert payload["run_date"] == "2026-01-02", payload
assert payload["skip_dates"] == ["2026-01-01"], payload
assert payload["would_skip"] is False, payload
assert payload["skip_reason"] == "configured_market_holiday", payload
PY

echo "portfolio remediation scheduler holiday skip verification passed"
