#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

ENV_FILE=""
JOB_ID=""
OUTPUT_DIR=""
TIMEOUT_SECONDS="3600"
RUN_DATE="${DATA_OPERATIONS_SCHEDULER_RUN_DATE:-$(TZ=America/New_York date +%Y-%m-%d)}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
COMMAND=()

usage() {
  cat <<'USAGE'
Usage:
  scripts/dry_run_data_operations_scheduler_operator_flow.sh --env-file PATH --job-id JOB_ID --output-dir PATH [options] -- COMMAND...

Options:
  --timeout-seconds N    Child command timeout checked by preflight/rendering. Default: 3600.
  --run-date YYYY-MM-DD  Scheduler business date for preflight. Default: current America/New_York date.

Rehearses the operator activation runbook without executing COMMAND, running
launchctl, writing LaunchAgents, or activating a scheduler.
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
    --output-dir)
      if [ "$#" -lt 2 ]; then
        echo "--output-dir requires a path." >&2
        exit 2
      fi
      OUTPUT_DIR="$2"
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

if [ -z "$OUTPUT_DIR" ]; then
  echo "Missing required --output-dir PATH." >&2
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
ABS_OUTPUT_DIR=$(absolute_path "$OUTPUT_DIR")

case "$ABS_ENV_FILE" in
  "$ABS_ROOT"|"$ABS_ROOT"/*)
    echo "Refusing to use data operations scheduler env file inside repository: $ABS_ENV_FILE" >&2
    exit 1
    ;;
esac

case "$ABS_OUTPUT_DIR" in
  "$ABS_ROOT"|"$ABS_ROOT"/*)
    echo "Refusing to write operator dry-run output inside repository: $ABS_OUTPUT_DIR" >&2
    exit 1
    ;;
esac

EVIDENCE_DIR="$ABS_OUTPUT_DIR/evidence"
RENDER_DIR="$ABS_OUTPUT_DIR/rendered"
mkdir -p "$EVIDENCE_DIR" "$RENDER_DIR"

READINESS_JSON="$EVIDENCE_DIR/env-readiness.json"
PREFLIGHT_JSON="$EVIDENCE_DIR/scheduler-preflight.json"
ALERT_OUTPUT="$EVIDENCE_DIR/alert-rule-validation.txt"
REPORT_JSON="$EVIDENCE_DIR/operator-dry-run.json"

scripts/check_data_operations_runtime_env.sh --env-file "$ABS_ENV_FILE" > "$READINESS_JSON"

scripts/run_data_operations_scheduler_job.sh \
  --env-file "$ABS_ENV_FILE" \
  --job-id "$JOB_ID" \
  --run-date "$RUN_DATE" \
  --timeout-seconds "$TIMEOUT_SECONDS" \
  --preflight-only \
  -- "${COMMAND[@]}" > "$PREFLIGHT_JSON"

MANIFEST_PATH=$(scripts/render_data_operations_scheduler_install.sh \
  --output-dir "$RENDER_DIR" \
  --env-file "$ABS_ENV_FILE" \
  --job-id "$JOB_ID" \
  --timeout-seconds "$TIMEOUT_SECONDS" \
  -- "${COMMAND[@]}")

"$PYTHON_BIN" scripts/validate_data_operations_alert_rules.py \
  ops/observability/data-operations-alert-rules.yml > "$ALERT_OUTPUT"

PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" - \
  "$JOB_ID" \
  "$ABS_OUTPUT_DIR" \
  "$READINESS_JSON" \
  "$PREFLIGHT_JSON" \
  "$MANIFEST_PATH" \
  "$ALERT_OUTPUT" \
  "$REPORT_JSON" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

from stockanalysis.operations.scheduler_operator_dry_run import (
    build_data_operations_scheduler_operator_dry_run_report,
)

job_id, output_dir, readiness_path, preflight_path, manifest_path, alert_output_path, report_path = sys.argv[1:]

readiness = json.loads(Path(readiness_path).read_text(encoding="utf-8"))
preflight = json.loads(Path(preflight_path).read_text(encoding="utf-8"))
manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
alert_output = Path(alert_output_path).read_text(encoding="utf-8")
plist_path = str(manifest.get("plist_path", ""))

report = build_data_operations_scheduler_operator_dry_run_report(
    job_id=job_id,
    output_dir=output_dir,
    readiness_report=readiness,
    preflight_report=preflight,
    install_manifest=manifest,
    alert_validation_output=alert_output,
    evidence_paths={
        "env_readiness_report": readiness_path,
        "scheduler_preflight_report": preflight_path,
        "install_manifest": manifest_path,
        "plist": plist_path,
        "alert_validation_output": alert_output_path,
    },
)

Path(report_path).write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
print(report_path)
PY
