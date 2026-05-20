#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

ACTIVATION_REQUEST_REPORT=""
DECISION_RECORD=""
OUTPUT_PATH=""
PYTHON_BIN="${PYTHON_BIN:-python3}"

usage() {
  cat <<'USAGE'
Usage:
  scripts/decide_data_operations_live_scheduler_activation.sh --activation-request-report PATH [options]

Options:
  --decision-record PATH  Repo-outside explicit user decision JSON.
  --output PATH           Repo-outside output JSON path. Prints to stdout when omitted.

Validates approve/deny user decisions for live scheduler activation. This
script never runs launchctl and never writes LaunchAgents.
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
    --activation-request-report)
      if [ "$#" -lt 2 ]; then
        echo "--activation-request-report requires a path." >&2
        exit 2
      fi
      ACTIVATION_REQUEST_REPORT="$2"
      shift 2
      ;;
    --decision-record)
      if [ "$#" -lt 2 ]; then
        echo "--decision-record requires a path." >&2
        exit 2
      fi
      DECISION_RECORD="$2"
      shift 2
      ;;
    --output)
      if [ "$#" -lt 2 ]; then
        echo "--output requires a path." >&2
        exit 2
      fi
      OUTPUT_PATH="$2"
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

if [ -z "$ACTIVATION_REQUEST_REPORT" ]; then
  echo "Missing required --activation-request-report PATH." >&2
  exit 1
fi

if [ ! -f "$ACTIVATION_REQUEST_REPORT" ]; then
  echo "Activation request report does not exist: $ACTIVATION_REQUEST_REPORT" >&2
  exit 1
fi

if [ -n "$DECISION_RECORD" ] && [ ! -f "$DECISION_RECORD" ]; then
  echo "Decision record does not exist: $DECISION_RECORD" >&2
  exit 1
fi

ABS_ROOT=$(absolute_path "$ROOT_DIR")
ABS_ACTIVATION_REQUEST_REPORT=$(absolute_path "$ACTIVATION_REQUEST_REPORT")
ABS_DECISION_RECORD=""
ABS_OUTPUT_PATH=""

case "$ABS_ACTIVATION_REQUEST_REPORT" in
  "$ABS_ROOT"|"$ABS_ROOT"/*)
    echo "Refusing to use activation request report inside repository: $ABS_ACTIVATION_REQUEST_REPORT" >&2
    exit 1
    ;;
esac

if [ -n "$DECISION_RECORD" ]; then
  ABS_DECISION_RECORD=$(absolute_path "$DECISION_RECORD")
  case "$ABS_DECISION_RECORD" in
    "$ABS_ROOT"|"$ABS_ROOT"/*)
      echo "Refusing to use decision record inside repository: $ABS_DECISION_RECORD" >&2
      exit 1
      ;;
  esac
fi

if [ -n "$OUTPUT_PATH" ]; then
  ABS_OUTPUT_PATH=$(absolute_path "$OUTPUT_PATH")
  case "$ABS_OUTPUT_PATH" in
    "$ABS_ROOT"|"$ABS_ROOT"/*)
      echo "Refusing to write activation decision output inside repository: $ABS_OUTPUT_PATH" >&2
      exit 1
      ;;
  esac
  mkdir -p "$(dirname "$ABS_OUTPUT_PATH")"
fi

PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" - \
  "$ABS_ACTIVATION_REQUEST_REPORT" \
  "$ABS_DECISION_RECORD" \
  "$ABS_OUTPUT_PATH" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

from stockanalysis.operations.scheduler_activation_decision import (
    build_data_operations_live_scheduler_activation_user_decision_report,
)

request_report_path, decision_record_path, output_path = sys.argv[1:]
request_report = json.loads(Path(request_report_path).read_text(encoding="utf-8"))
decision_record = None
if decision_record_path:
    decision_record = json.loads(Path(decision_record_path).read_text(encoding="utf-8"))

report = build_data_operations_live_scheduler_activation_user_decision_report(
    activation_request_report=request_report,
    decision_record=decision_record,
    activation_request_report_path=request_report_path,
    decision_record_path=decision_record_path,
)
text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
if output_path:
    Path(output_path).write_text(text, encoding="utf-8")
    print(output_path)
else:
    print(text, end="")
PY
