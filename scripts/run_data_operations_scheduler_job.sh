#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

ENV_FILE=""
JOB_ID=""
TIMEOUT_SECONDS="3600"
RUN_DATE="${DATA_OPERATIONS_SCHEDULER_RUN_DATE:-$(TZ=America/New_York date +%Y-%m-%d)}"
SKIP_DATES="${DATA_OPERATIONS_SCHEDULER_SKIP_DATES:-}"
SKIP_REASON="${DATA_OPERATIONS_SCHEDULER_SKIP_REASON:-configured_skip_date}"
PREFLIGHT_ONLY="false"
PYTHON_BIN="${PYTHON_BIN:-python3}"
COMMAND=()

usage() {
  cat <<'USAGE'
Usage:
  scripts/run_data_operations_scheduler_job.sh --env-file PATH --job-id JOB_ID [options] -- COMMAND...

Options:
  --preflight-only        Validate env/job/command and print JSON without running COMMAND.
  --timeout-seconds N    Child command timeout for data-operations-run. Default: 3600.
  --run-date YYYY-MM-DD  Scheduler business date. Default: current America/New_York date.
  --skip-dates DATES     Comma/space separated ISO dates to skip.
  --skip-reason TEXT     Skip reason for configured skip-date hits.

This wrapper is the scheduler activation boundary. It does not install cron,
launchd, GitHub Actions, or hosted scheduler artifacts.
USAGE
}

absolute_path() {
  python3 - "$1" <<'PY'
import os
import sys

print(os.path.abspath(sys.argv[1]))
PY
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
    --job-id)
      if [ "$#" -lt 2 ]; then
        echo "--job-id requires a value." >&2
        exit 2
      fi
      JOB_ID="$2"
      shift 2
      ;;
    --timeout-seconds)
      if [ "$#" -lt 2 ]; then
        echo "--timeout-seconds requires a value." >&2
        exit 2
      fi
      TIMEOUT_SECONDS="$2"
      shift 2
      ;;
    --run-date)
      if [ "$#" -lt 2 ]; then
        echo "--run-date requires a value." >&2
        exit 2
      fi
      RUN_DATE="$2"
      shift 2
      ;;
    --skip-dates)
      if [ "$#" -lt 2 ]; then
        echo "--skip-dates requires a value." >&2
        exit 2
      fi
      SKIP_DATES="$2"
      shift 2
      ;;
    --skip-reason)
      if [ "$#" -lt 2 ]; then
        echo "--skip-reason requires a value." >&2
        exit 2
      fi
      SKIP_REASON="$2"
      shift 2
      ;;
    --preflight-only)
      PREFLIGHT_ONLY="true"
      shift
      ;;
    --help)
      usage
      exit 0
      ;;
    --)
      shift
      COMMAND=("$@")
      break
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

if [ -z "$JOB_ID" ]; then
  echo "Missing required --job-id JOB_ID." >&2
  exit 1
fi

if [ "${#COMMAND[@]}" -eq 0 ]; then
  echo "Missing command after --." >&2
  exit 1
fi

case "$TIMEOUT_SECONDS" in
  ""|*[!0-9]*)
    echo "--timeout-seconds must be a positive integer." >&2
    exit 2
    ;;
esac
if [ "$TIMEOUT_SECONDS" -le 0 ]; then
  echo "--timeout-seconds must be greater than 0." >&2
  exit 2
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "Env file does not exist: $ENV_FILE" >&2
  exit 1
fi

ABS_ROOT=$(absolute_path "$ROOT_DIR")
ABS_ENV_FILE=$(absolute_path "$ENV_FILE")

case "$ABS_ENV_FILE" in
  "$ABS_ROOT"|"$ABS_ROOT"/*)
    echo "Refusing to use data operations scheduler env file inside repository: $ABS_ENV_FILE" >&2
    exit 1
    ;;
esac

TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/stockanalysis-data-ops-scheduler.XXXXXX")
trap 'rm -rf "$TMP_DIR"' EXIT

READINESS_JSON="$TMP_DIR/readiness.json"
PREFLIGHT_JSON="$TMP_DIR/preflight.json"

scripts/check_data_operations_runtime_env.sh --env-file "$ABS_ENV_FILE" > "$READINESS_JSON"

set -a
. "$ABS_ENV_FILE"
set +a
export DATA_OPERATIONS_SCHEDULER_RUN_DATE="$RUN_DATE"

if [ -z "${STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT:-}" ]; then
  echo "Missing required environment variable: STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT" >&2
  exit 1
fi

PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" - "$READINESS_JSON" "$JOB_ID" "$RUN_DATE" "$SKIP_DATES" "$SKIP_REASON" "$TIMEOUT_SECONDS" "${COMMAND[@]}" > "$PREFLIGHT_JSON" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

from stockanalysis.operations.scheduler_boundary import build_data_operations_scheduler_preflight_report

readiness_path, job_id, run_date, skip_dates, skip_reason, timeout_seconds, *command = sys.argv[1:]
readiness = json.loads(Path(readiness_path).read_text(encoding="utf-8"))
report = build_data_operations_scheduler_preflight_report(
    job_id=job_id,
    readiness_report=readiness,
    command_argv=command,
    run_date=run_date,
    skip_dates=skip_dates,
    skip_reason=skip_reason,
    timeout_seconds=int(timeout_seconds),
)
print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
PY

if [ "$PREFLIGHT_ONLY" = "true" ]; then
  cat "$PREFLIGHT_JSON"
  exit 0
fi

WOULD_SKIP=$(PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" - "$PREFLIGHT_JSON" <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
print("true" if payload["would_skip"] else "false")
PY
)

if [ "$WOULD_SKIP" = "true" ]; then
  RUN_STAMP=$(date -u +"%Y%m%dT%H%M%SZ")
  SAFE_JOB_ID=$(printf '%s' "$JOB_ID" | tr -c '[:alnum:]_-' '-')
  SKIP_DIR="$STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT/${RUN_STAMP}_${SAFE_JOB_ID}_scheduler-skip"
  mkdir -p "$SKIP_DIR"
  STDOUT_JSON="$SKIP_DIR/stdout.json"
  STDERR_LOG="$SKIP_DIR/stderr.log"
  METADATA_JSON="$SKIP_DIR/metadata.json"
  printf 'scheduler skipped job_id=%s run_date=%s reason=%s\n' "$JOB_ID" "$RUN_DATE" "$SKIP_REASON" > "$STDERR_LOG"
  PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" - "$JOB_ID" "$RUN_DATE" "$SKIP_DATES" "$SKIP_REASON" "$SKIP_DIR" "$STDOUT_JSON" "$STDERR_LOG" "$METADATA_JSON" <<'PY'
from __future__ import annotations

import json
import sys

from stockanalysis.operations.scheduler_boundary import build_data_operations_scheduler_skip_report

job_id, run_date, skip_dates, skip_reason, skip_dir, stdout_json, stderr_log, metadata_json = sys.argv[1:]
payload = build_data_operations_scheduler_skip_report(
    job_id=job_id,
    run_date=run_date,
    skip_dates=skip_dates,
    skip_reason=skip_reason,
)
payload.update(
    {
        "artifact_dir": skip_dir,
        "stdout_json_path": stdout_json,
        "stderr_path": stderr_log,
        "metadata_path": metadata_json,
    }
)
with open(stdout_json, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=2, ensure_ascii=False, sort_keys=True)
    handle.write("\n")
with open(metadata_json, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=2, ensure_ascii=False, sort_keys=True)
    handle.write("\n")
print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
PY
  exit 0
fi

PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m stockanalysis.ingest.cli \
  data-operations-run \
  --job-id "$JOB_ID" \
  --artifact-root "$STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT" \
  --timeout-seconds "$TIMEOUT_SECONDS" \
  -- "${COMMAND[@]}"
