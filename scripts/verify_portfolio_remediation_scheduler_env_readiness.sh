#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
ARTIFACT_ROOT=$(mktemp -d /tmp/stockanalysis-scheduler-env-readiness.XXXXXX)
TEMPLATE_ENV="$ARTIFACT_ROOT/scheduler.template.env"
VALID_ENV="$ARTIFACT_ROOT/scheduler.valid.env"
READINESS_OUTPUT="$ARTIFACT_ROOT/readiness.json"
INSTALL_PLIST_PATH="$ARTIFACT_ROOT/install-plist-path.txt"

cleanup() {
  rm -rf "$ARTIFACT_ROOT"
}

trap cleanup EXIT

cd "$ROOT_DIR"

bash -n scripts/render_portfolio_remediation_scheduler_env_template.sh
bash -n scripts/check_portfolio_remediation_scheduler_runtime_env.sh
bash -n scripts/verify_portfolio_remediation_scheduler_env_readiness.sh
bash -n scripts/run_portfolio_remediation_daily_scheduler.sh
bash -n scripts/install_portfolio_remediation_scheduler.sh

if scripts/render_portfolio_remediation_scheduler_env_template.sh --output "$ROOT_DIR/scheduler.env" >/dev/null 2>&1; then
  echo "renderer accepted a repo-internal output path" >&2
  exit 1
fi

scripts/render_portfolio_remediation_scheduler_env_template.sh --output "$TEMPLATE_ENV" >/dev/null

if scripts/check_portfolio_remediation_scheduler_runtime_env.sh --env-file "$TEMPLATE_ENV" >/dev/null 2>&1; then
  echo "readiness check accepted an unedited template" >&2
  exit 1
fi

cat > "$VALID_ENV" <<ENV
STOCKANALYSIS_PSQL_COMMAND="python3 -c print('succeeded')"
PORTFOLIO_REMEDIATION_AS_OF_DATE="2024-11-01"
PORTFOLIO_REMEDIATION_UNIVERSE_VERSION="fixture-v1"
PORTFOLIO_REMEDIATION_COVERAGE_MEASUREMENT_END_DATE="2024-12-02"
PORTFOLIO_REMEDIATION_PORTFOLIO_NAME="Long Term Paper"
PORTFOLIO_REMEDIATION_STRATEGY_NAME="long_term_core"
PORTFOLIO_REMEDIATION_HORIZON_TYPE="long_term"
PORTFOLIO_REMEDIATION_TICKET_LIMIT="5"
PORTFOLIO_REMEDIATION_TICKET_STATUS="open"
PORTFOLIO_REMEDIATION_ARTIFACT_ROOT="$ARTIFACT_ROOT/scheduler-artifacts"
ENV

chmod 600 "$VALID_ENV"

scripts/check_portfolio_remediation_scheduler_runtime_env.sh --env-file "$VALID_ENV" > "$READINESS_OUTPUT"

python3 - "$READINESS_OUTPUT" "$VALID_ENV" "$ARTIFACT_ROOT/scheduler-artifacts" <<'PY'
import json
import sys

output_path, env_file, artifact_root = sys.argv[1:]

with open(output_path, "r", encoding="utf-8") as handle:
    payload = json.load(handle)

assert payload["runtime_env_readiness"] == "passed", payload
assert payload["env_file"] == env_file, payload
assert payload["artifact_root"] == artifact_root, payload
assert payload["psql_command_argv0"] == "python3", payload
assert payload["wrapper_preflight"] == "passed", payload
PY

PORTFOLIO_REMEDIATION_INSTALL_ARTIFACT_ROOT="$ARTIFACT_ROOT/install" \
scripts/install_portfolio_remediation_scheduler.sh --dry-run --env-file "$VALID_ENV" > "$INSTALL_PLIST_PATH"

python3 - "$INSTALL_PLIST_PATH" <<'PY'
import os
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    plist_path = handle.read().strip()

assert os.path.isfile(plist_path), plist_path
assert plist_path.endswith("com.stockanalysis.portfolio-remediation-daily.plist"), plist_path
PY

echo "portfolio remediation scheduler env readiness verification passed"
