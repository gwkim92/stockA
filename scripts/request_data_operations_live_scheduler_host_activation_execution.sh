#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

HOST_ACTIVATION_PLAN_REPORT=""
OUTPUT_PATH=""
REQUEST_NOTE=""
PYTHON_BIN="${PYTHON_BIN:-python3}"

usage() {
  cat <<'USAGE'
Usage:
  scripts/request_data_operations_live_scheduler_host_activation_execution.sh --host-activation-plan-report PATH [options]

Options:
  --output PATH        Repo-outside output JSON path. Prints to stdout when omitted.
  --request-note TEXT  Optional secret-free operator note.

Creates a host activation execution request packet for explicit execution
approval. This script never runs launchctl and never writes LaunchAgents.
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
    --host-activation-plan-report)
      if [ "$#" -lt 2 ]; then
        echo "--host-activation-plan-report requires a path." >&2
        exit 2
      fi
      HOST_ACTIVATION_PLAN_REPORT="$2"
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
    --request-note)
      if [ "$#" -lt 2 ]; then
        echo "--request-note requires text." >&2
        exit 2
      fi
      REQUEST_NOTE="$2"
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

if [ -z "$HOST_ACTIVATION_PLAN_REPORT" ]; then
  echo "Missing required --host-activation-plan-report PATH." >&2
  exit 1
fi

if [ ! -f "$HOST_ACTIVATION_PLAN_REPORT" ]; then
  echo "Host activation plan report does not exist: $HOST_ACTIVATION_PLAN_REPORT" >&2
  exit 1
fi

ABS_ROOT=$(absolute_path "$ROOT_DIR")
ABS_HOST_ACTIVATION_PLAN_REPORT=$(absolute_path "$HOST_ACTIVATION_PLAN_REPORT")
ABS_OUTPUT_PATH=""

case "$ABS_HOST_ACTIVATION_PLAN_REPORT" in
  "$ABS_ROOT"|"$ABS_ROOT"/*)
    echo "Refusing to use host activation plan report inside repository: $ABS_HOST_ACTIVATION_PLAN_REPORT" >&2
    exit 1
    ;;
esac

if [ -n "$OUTPUT_PATH" ]; then
  ABS_OUTPUT_PATH=$(absolute_path "$OUTPUT_PATH")
  case "$ABS_OUTPUT_PATH" in
    "$ABS_ROOT"|"$ABS_ROOT"/*)
      echo "Refusing to write host activation execution request output inside repository: $ABS_OUTPUT_PATH" >&2
      exit 1
      ;;
  esac
  mkdir -p "$(dirname "$ABS_OUTPUT_PATH")"
fi

PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" - \
  "$ABS_HOST_ACTIVATION_PLAN_REPORT" \
  "$ABS_OUTPUT_PATH" \
  "$REQUEST_NOTE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

from stockanalysis.operations.scheduler_activation_execution_request import (
    build_data_operations_live_scheduler_host_activation_execution_request_report,
)

host_activation_plan_report_path, output_path, request_note = sys.argv[1:]
host_activation_plan_report = json.loads(Path(host_activation_plan_report_path).read_text(encoding="utf-8"))

report = build_data_operations_live_scheduler_host_activation_execution_request_report(
    host_activation_plan_report=host_activation_plan_report,
    host_activation_plan_report_path=host_activation_plan_report_path,
    request_note=request_note,
)
text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
if output_path:
    Path(output_path).write_text(text, encoding="utf-8")
    print(output_path)
else:
    print(text, end="")
PY
