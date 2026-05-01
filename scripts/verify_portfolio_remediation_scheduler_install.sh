#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
ARTIFACT_ROOT=$(mktemp -d /tmp/stockanalysis-scheduler-install.XXXXXX)
ENV_FILE="$ARTIFACT_ROOT/scheduler.env"
PLIST_PATH_FILE="$ARTIFACT_ROOT/plist-path.txt"

cleanup() {
  rm -rf "$ARTIFACT_ROOT"
}

trap cleanup EXIT

cat > "$ENV_FILE" <<'ENV'
STOCKANALYSIS_PSQL_COMMAND="psql postgresql://example.invalid/stockanalysis"
PORTFOLIO_REMEDIATION_AS_OF_DATE="2024-11-01"
PORTFOLIO_REMEDIATION_UNIVERSE_VERSION="fixture-v1"
PORTFOLIO_REMEDIATION_COVERAGE_MEASUREMENT_END_DATE="2024-12-02"
PORTFOLIO_REMEDIATION_ARTIFACT_ROOT="/tmp/stockanalysis-remediation-scheduler"
ENV

bash -n "$ROOT_DIR/scripts/install_portfolio_remediation_scheduler.sh"
bash -n "$ROOT_DIR/scripts/run_portfolio_remediation_daily_scheduler.sh"

PORTFOLIO_REMEDIATION_INSTALL_ARTIFACT_ROOT="$ARTIFACT_ROOT/rendered" \
"$ROOT_DIR/scripts/install_portfolio_remediation_scheduler.sh" --dry-run --env-file "$ENV_FILE" > "$PLIST_PATH_FILE"

PLIST_PATH=$(cat "$PLIST_PATH_FILE")

python3 - "$PLIST_PATH" "$ROOT_DIR" "$ENV_FILE" <<'PY'
import plistlib
import sys

plist_path, root_dir, env_file = sys.argv[1:]

with open(plist_path, "rb") as handle:
    payload = plistlib.load(handle)

assert payload["Label"] == "com.stockanalysis.portfolio-remediation-daily", payload
assert payload["WorkingDirectory"] == root_dir, payload
assert payload["ProgramArguments"][0] == "/bin/bash", payload
command = payload["ProgramArguments"][2]
assert env_file in command, payload
assert "scripts/run_portfolio_remediation_daily_scheduler.sh" in command, payload
assert payload["RunAtLoad"] is False, payload
schedule = payload["StartCalendarInterval"]
assert len(schedule) == 5, payload
assert {item["Weekday"] for item in schedule} == {2, 3, 4, 5, 6}, payload
assert {item["Hour"] for item in schedule} == {18}, payload
assert {item["Minute"] for item in schedule} == {30}, payload
assert payload["StandardOutPath"].endswith(".stdout.log"), payload
assert payload["StandardErrorPath"].endswith(".stderr.log"), payload
PY

case "$PLIST_PATH" in
  "$HOME/Library/LaunchAgents/"*)
    echo "Dry-run rendered to host scheduler directory: $PLIST_PATH" >&2
    exit 1
    ;;
esac

echo "portfolio remediation scheduler install dry-run verification passed"
