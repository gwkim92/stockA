#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
ARTIFACT_ROOT=$(mktemp -d /tmp/stockanalysis-scheduler-activation.XXXXXX)
MISSING_ENV_LOG="$ARTIFACT_ROOT/missing-env.log"

cleanup() {
  rm -rf "$ARTIFACT_ROOT"
}

trap cleanup EXIT

bash -n "$ROOT_DIR/scripts/run_portfolio_remediation_daily_scheduler.sh"

if "$ROOT_DIR/scripts/run_portfolio_remediation_daily_scheduler.sh" --preflight-only > /dev/null 2> "$MISSING_ENV_LOG"; then
  echo "Expected preflight to fail when required env vars are missing." >&2
  exit 1
fi

rg -q "Missing required environment variable: STOCKANALYSIS_PSQL_COMMAND" "$MISSING_ENV_LOG"

STOCKANALYSIS_PSQL_COMMAND="psql postgresql://example.invalid/stockanalysis" \
PORTFOLIO_REMEDIATION_AS_OF_DATE="2024-11-01" \
PORTFOLIO_REMEDIATION_UNIVERSE_VERSION="fixture-v1" \
PORTFOLIO_REMEDIATION_COVERAGE_MEASUREMENT_END_DATE="2024-12-02" \
PORTFOLIO_REMEDIATION_ARTIFACT_ROOT="$ARTIFACT_ROOT" \
"$ROOT_DIR/scripts/run_portfolio_remediation_daily_scheduler.sh" --preflight-only > "$ARTIFACT_ROOT/preflight.json"

python3 - "$ARTIFACT_ROOT/preflight.json" "$ARTIFACT_ROOT" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    payload = json.load(handle)

assert payload["preflight"] == "passed", payload
assert payload["artifact_root"] == sys.argv[2], payload
assert payload["json_path"].endswith("-portfolio-remediation-daily.json"), payload
assert payload["stderr_path"].endswith("-portfolio-remediation-daily.stderr.log"), payload
assert payload["run_date"], payload
assert payload["skip_dates"] == [], payload
assert payload["would_skip"] is False, payload
assert payload["skip_reason"] == "configured_market_holiday", payload
PY

for activation_path in \
  ".github/workflows/portfolio-remediation-scheduler.yml" \
  "cron/portfolio-remediation-daily.cron" \
  "launchd/com.stockanalysis.portfolio-remediation.plist"
do
  if [ -e "$ROOT_DIR/$activation_path" ]; then
    echo "Unexpected scheduler activation artifact exists: $activation_path" >&2
    exit 1
  fi
done

echo "portfolio remediation scheduler activation preflight verification passed"
