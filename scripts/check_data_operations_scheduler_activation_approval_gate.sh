#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

OPERATOR_DRY_RUN_REPORT=""
APPROVAL_RECORD=""
OUTPUT_PATH=""
PYTHON_BIN="${PYTHON_BIN:-python3}"

usage() {
  cat <<'USAGE'
Usage:
  scripts/check_data_operations_scheduler_activation_approval_gate.sh --operator-dry-run-report PATH [options]

Options:
  --approval-record PATH  Repo-outside explicit approval JSON.
  --output PATH           Repo-outside output JSON path. Prints to stdout when omitted.

Checks whether Data Operations scheduler activation is blocked or explicitly
approved. This script never runs launchctl and never writes LaunchAgents.
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
    --operator-dry-run-report)
      if [ "$#" -lt 2 ]; then
        echo "--operator-dry-run-report requires a path." >&2
        exit 2
      fi
      OPERATOR_DRY_RUN_REPORT="$2"
      shift 2
      ;;
    --approval-record)
      if [ "$#" -lt 2 ]; then
        echo "--approval-record requires a path." >&2
        exit 2
      fi
      APPROVAL_RECORD="$2"
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

if [ -z "$OPERATOR_DRY_RUN_REPORT" ]; then
  echo "Missing required --operator-dry-run-report PATH." >&2
  exit 1
fi

if [ ! -f "$OPERATOR_DRY_RUN_REPORT" ]; then
  echo "Operator dry-run report does not exist: $OPERATOR_DRY_RUN_REPORT" >&2
  exit 1
fi

if [ -n "$APPROVAL_RECORD" ] && [ ! -f "$APPROVAL_RECORD" ]; then
  echo "Approval record does not exist: $APPROVAL_RECORD" >&2
  exit 1
fi

ABS_ROOT=$(absolute_path "$ROOT_DIR")
ABS_OPERATOR_DRY_RUN_REPORT=$(absolute_path "$OPERATOR_DRY_RUN_REPORT")
ABS_APPROVAL_RECORD=""
ABS_OUTPUT_PATH=""

case "$ABS_OPERATOR_DRY_RUN_REPORT" in
  "$ABS_ROOT"|"$ABS_ROOT"/*)
    echo "Refusing to use operator dry-run report inside repository: $ABS_OPERATOR_DRY_RUN_REPORT" >&2
    exit 1
    ;;
esac

if [ -n "$APPROVAL_RECORD" ]; then
  ABS_APPROVAL_RECORD=$(absolute_path "$APPROVAL_RECORD")
  case "$ABS_APPROVAL_RECORD" in
    "$ABS_ROOT"|"$ABS_ROOT"/*)
      echo "Refusing to use approval record inside repository: $ABS_APPROVAL_RECORD" >&2
      exit 1
      ;;
  esac
fi

if [ -n "$OUTPUT_PATH" ]; then
  ABS_OUTPUT_PATH=$(absolute_path "$OUTPUT_PATH")
  case "$ABS_OUTPUT_PATH" in
    "$ABS_ROOT"|"$ABS_ROOT"/*)
      echo "Refusing to write approval gate output inside repository: $ABS_OUTPUT_PATH" >&2
      exit 1
      ;;
  esac
  mkdir -p "$(dirname "$ABS_OUTPUT_PATH")"
fi

PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" - \
  "$ABS_OPERATOR_DRY_RUN_REPORT" \
  "$ABS_APPROVAL_RECORD" \
  "$ABS_OUTPUT_PATH" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

from stockanalysis.operations.scheduler_activation_approval import (
    build_data_operations_scheduler_activation_approval_gate_report,
)

operator_report_path, approval_record_path, output_path = sys.argv[1:]
operator_report = json.loads(Path(operator_report_path).read_text(encoding="utf-8"))
evidence_paths = dict(operator_report.get("evidence_paths", {}))
evidence_paths["operator_dry_run_report"] = operator_report_path
operator_report["evidence_paths"] = evidence_paths

approval_record = None
if approval_record_path:
    approval_record = json.loads(Path(approval_record_path).read_text(encoding="utf-8"))

report = build_data_operations_scheduler_activation_approval_gate_report(
    operator_dry_run_report=operator_report,
    approval_record=approval_record,
    approval_record_path=approval_record_path,
)
text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
if output_path:
    Path(output_path).write_text(text, encoding="utf-8")
    print(output_path)
else:
    print(text, end="")
PY
