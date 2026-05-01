#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
ENV_FILE=""
WRAPPER_PATH="$ROOT_DIR/scripts/run_portfolio_remediation_daily_scheduler.sh"

usage() {
  cat <<'USAGE'
Usage:
  scripts/check_portfolio_remediation_scheduler_runtime_env.sh --env-file PATH

Checks a trusted scheduler env file without connecting to the runtime DB.
USAGE
}

absolute_path() {
  python3 - "$1" <<'PY'
import os
import sys

print(os.path.abspath(sys.argv[1]))
PY
}

require_env() {
  local name="$1"
  if [ -z "${!name:-}" ]; then
    echo "Missing required environment variable: $name" >&2
    exit 1
  fi
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --env-file)
      if [ "$#" -lt 2 ]; then
        echo "--env-file requires a path." >&2
        exit 2
      fi
      ENV_FILE="$2"
      shift 2
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ -z "$ENV_FILE" ]; then
  echo "Missing required --env-file PATH." >&2
  exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "Env file does not exist: $ENV_FILE" >&2
  exit 1
fi

if [ ! -x "$WRAPPER_PATH" ]; then
  echo "Scheduler wrapper is missing or not executable: $WRAPPER_PATH" >&2
  exit 1
fi

ABS_ROOT=$(absolute_path "$ROOT_DIR")
ABS_ENV_FILE=$(absolute_path "$ENV_FILE")

case "$ABS_ENV_FILE" in
  "$ABS_ROOT"|"$ABS_ROOT"/*)
    echo "Refusing to use scheduler env file inside repository: $ABS_ENV_FILE" >&2
    exit 1
    ;;
esac

set -a
. "$ABS_ENV_FILE"
set +a

require_env "STOCKANALYSIS_PSQL_COMMAND"
require_env "PORTFOLIO_REMEDIATION_AS_OF_DATE"
require_env "PORTFOLIO_REMEDIATION_UNIVERSE_VERSION"
require_env "PORTFOLIO_REMEDIATION_COVERAGE_MEASUREMENT_END_DATE"
require_env "PORTFOLIO_REMEDIATION_ARTIFACT_ROOT"

PORTFOLIO_REMEDIATION_TICKET_LIMIT="${PORTFOLIO_REMEDIATION_TICKET_LIMIT:-50}"

case "$PORTFOLIO_REMEDIATION_TICKET_LIMIT" in
  ""|*[!0-9]*)
    echo "PORTFOLIO_REMEDIATION_TICKET_LIMIT must be a positive integer." >&2
    exit 1
    ;;
esac

if [ "$PORTFOLIO_REMEDIATION_TICKET_LIMIT" -le 0 ]; then
  echo "PORTFOLIO_REMEDIATION_TICKET_LIMIT must be greater than 0." >&2
  exit 1
fi

python3 - "$ABS_ENV_FILE" "$ABS_ROOT" <<'PY'
import datetime as dt
import json
import os
import shlex
import shutil
import subprocess
import sys

env_file, root_dir = sys.argv[1:]

required = [
    "STOCKANALYSIS_PSQL_COMMAND",
    "PORTFOLIO_REMEDIATION_AS_OF_DATE",
    "PORTFOLIO_REMEDIATION_UNIVERSE_VERSION",
    "PORTFOLIO_REMEDIATION_COVERAGE_MEASUREMENT_END_DATE",
    "PORTFOLIO_REMEDIATION_ARTIFACT_ROOT",
]
placeholder_tokens = [
    "CHANGE_ME",
    "USER:PASSWORD@HOST",
    "YYYY-MM-DD",
    "/absolute/path",
    "example.invalid",
    "replace-with",
]

for name in required:
    value = os.environ[name]
    if any(token in value for token in placeholder_tokens):
        raise SystemExit(f"{name} still contains a placeholder value.")

for name in [
    "PORTFOLIO_REMEDIATION_AS_OF_DATE",
    "PORTFOLIO_REMEDIATION_COVERAGE_MEASUREMENT_END_DATE",
]:
    try:
        dt.date.fromisoformat(os.environ[name])
    except ValueError as exc:
        raise SystemExit(f"{name} must be ISO date YYYY-MM-DD.") from exc

artifact_root = os.environ["PORTFOLIO_REMEDIATION_ARTIFACT_ROOT"]
if not os.path.isabs(artifact_root):
    raise SystemExit("PORTFOLIO_REMEDIATION_ARTIFACT_ROOT must be absolute.")
os.makedirs(artifact_root, exist_ok=True)
if not os.access(artifact_root, os.W_OK):
    raise SystemExit(f"Artifact root is not writable: {artifact_root}")

try:
    psql_argv = shlex.split(os.environ["STOCKANALYSIS_PSQL_COMMAND"])
except ValueError as exc:
    raise SystemExit(f"Invalid STOCKANALYSIS_PSQL_COMMAND: {exc}") from exc
if not psql_argv:
    raise SystemExit("STOCKANALYSIS_PSQL_COMMAND is empty.")
if shutil.which(psql_argv[0]) is None:
    raise SystemExit(f"Missing command for STOCKANALYSIS_PSQL_COMMAND: {psql_argv[0]}")

wrapper = os.path.join(root_dir, "scripts", "run_portfolio_remediation_daily_scheduler.sh")
completed = subprocess.run(
    [wrapper, "--preflight-only"],
    text=True,
    capture_output=True,
    check=False,
)
if completed.returncode != 0:
    stderr = completed.stderr.strip() or completed.stdout.strip() or "wrapper preflight failed"
    raise SystemExit(stderr)

try:
    preflight_payload = json.loads(completed.stdout)
except json.JSONDecodeError as exc:
    raise SystemExit("Wrapper preflight output is not valid JSON.") from exc
if preflight_payload.get("preflight") != "passed":
    raise SystemExit(f"Unexpected wrapper preflight payload: {preflight_payload!r}")

print(
    json.dumps(
        {
            "runtime_env_readiness": "passed",
            "env_file": env_file,
            "artifact_root": artifact_root,
            "psql_command_argv0": psql_argv[0],
            "wrapper_preflight": preflight_payload["preflight"],
        },
        ensure_ascii=False,
        indent=2,
    )
)
PY
