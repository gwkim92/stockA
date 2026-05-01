#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
ENV_FILE=""
WRAPPER_PATH="$ROOT_DIR/scripts/run_portfolio_remediation_daily_scheduler.sh"

usage() {
  cat <<'USAGE'
Usage:
  scripts/smoke_portfolio_remediation_scheduler_runtime_env.sh --env-file PATH

The env file is sourced as shell. Use only trusted files.
USAGE
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

set -a
. "$ENV_FILE"
set +a

if [ -z "${STOCKANALYSIS_PSQL_COMMAND:-}" ]; then
  echo "Missing required environment variable after sourcing env file: STOCKANALYSIS_PSQL_COMMAND" >&2
  exit 1
fi

cd "$ROOT_DIR"

json_path=$("$WRAPPER_PATH")
stderr_path="${json_path%.json}.stderr.log"

python3 - "$json_path" "$stderr_path" <<'PY'
import json
import os
import shlex
import subprocess
import sys

json_path, stderr_path = sys.argv[1:]

if not os.path.isfile(json_path):
    raise SystemExit(f"Missing scheduler JSON artifact: {json_path}")
if not os.path.isfile(stderr_path):
    raise SystemExit(f"Missing scheduler stderr artifact: {stderr_path}")

with open(json_path, "r", encoding="utf-8") as handle:
    payload = json.load(handle)

if payload.get("report_name") != "portfolio_remediation_daily_automation":
    raise SystemExit(f"Unexpected report_name: {payload.get('report_name')!r}")
if not payload.get("run_id"):
    raise SystemExit("Missing top-level run_id in scheduler output.")

ticket_report = payload.get("ticket_report") or {}
tickets = ticket_report.get("tickets") or []
matching_tickets = [
    ticket
    for ticket in tickets
    if ticket.get("symbol") == "BABA"
    and ticket.get("status") == "open"
    and ticket.get("remediation_type") == "thesis_remediation"
    and ticket.get("suggested_runner") == "thesis_or_position_link_review"
]
if not matching_tickets:
    raise SystemExit("Missing expected BABA open thesis remediation ticket.")

command_text = os.environ.get("STOCKANALYSIS_PSQL_COMMAND", "")
try:
    command = shlex.split(command_text)
except ValueError as exc:
    raise SystemExit(f"Invalid STOCKANALYSIS_PSQL_COMMAND: {exc}") from exc
if not command:
    raise SystemExit("STOCKANALYSIS_PSQL_COMMAND is empty.")

sql = """
select status
from ops.pipeline_run
where pipeline_name = 'portfolio_remediation_daily_automation'
order by run_id desc
limit 1;
"""
completed = subprocess.run(
    [*command, "-v", "ON_ERROR_STOP=1", "-X", "-q", "-t", "-A"],
    input=sql,
    text=True,
    capture_output=True,
    check=False,
)
if completed.returncode != 0:
    stderr = completed.stderr.strip() or completed.stdout.strip() or "psql command failed"
    raise SystemExit(stderr)
status = completed.stdout.strip().splitlines()[-1].strip()
if status != "succeeded":
    raise SystemExit(f"Unexpected latest daily automation status: {status!r}")

print(
    json.dumps(
        {
            "runtime_env_smoke": "passed",
            "json_path": json_path,
            "stderr_path": stderr_path,
            "run_id": payload["run_id"],
            "ticket_count": ticket_report.get("ticket_count"),
            "latest_daily_automation_status": status,
        },
        ensure_ascii=False,
        indent=2,
    )
)
PY
