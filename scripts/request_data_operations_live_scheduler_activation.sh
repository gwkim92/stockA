#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

APPROVAL_GATE_REPORT=""
OPERATOR_DRY_RUN_REPORT=""
OUTPUT_PATH=""
REQUEST_NOTE=""
PYTHON_BIN="${PYTHON_BIN:-python3}"

usage() {
  cat <<'USAGE'
Usage:
  scripts/request_data_operations_live_scheduler_activation.sh --approval-gate-report PATH [options]

Options:
  --operator-dry-run-report PATH  Repo-outside operator dry-run JSON. Defaults to the path recorded in the gate report.
  --output PATH                   Repo-outside output JSON path. Prints to stdout when omitted.
  --request-note TEXT             Optional secret-free operator note.

Creates a live scheduler activation request packet for explicit user approval.
This script never runs launchctl and never writes LaunchAgents.
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
    --approval-gate-report)
      if [ "$#" -lt 2 ]; then
        echo "--approval-gate-report requires a path." >&2
        exit 2
      fi
      APPROVAL_GATE_REPORT="$2"
      shift 2
      ;;
    --operator-dry-run-report)
      if [ "$#" -lt 2 ]; then
        echo "--operator-dry-run-report requires a path." >&2
        exit 2
      fi
      OPERATOR_DRY_RUN_REPORT="$2"
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

if [ -z "$APPROVAL_GATE_REPORT" ]; then
  echo "Missing required --approval-gate-report PATH." >&2
  exit 1
fi

if [ ! -f "$APPROVAL_GATE_REPORT" ]; then
  echo "Approval gate report does not exist: $APPROVAL_GATE_REPORT" >&2
  exit 1
fi

if [ -n "$OPERATOR_DRY_RUN_REPORT" ] && [ ! -f "$OPERATOR_DRY_RUN_REPORT" ]; then
  echo "Operator dry-run report does not exist: $OPERATOR_DRY_RUN_REPORT" >&2
  exit 1
fi

ABS_ROOT=$(absolute_path "$ROOT_DIR")
ABS_APPROVAL_GATE_REPORT=$(absolute_path "$APPROVAL_GATE_REPORT")
ABS_OPERATOR_DRY_RUN_REPORT=""
ABS_OUTPUT_PATH=""

case "$ABS_APPROVAL_GATE_REPORT" in
  "$ABS_ROOT"|"$ABS_ROOT"/*)
    echo "Refusing to use approval gate report inside repository: $ABS_APPROVAL_GATE_REPORT" >&2
    exit 1
    ;;
esac

if [ -n "$OPERATOR_DRY_RUN_REPORT" ]; then
  ABS_OPERATOR_DRY_RUN_REPORT=$(absolute_path "$OPERATOR_DRY_RUN_REPORT")
  case "$ABS_OPERATOR_DRY_RUN_REPORT" in
    "$ABS_ROOT"|"$ABS_ROOT"/*)
      echo "Refusing to use operator dry-run report inside repository: $ABS_OPERATOR_DRY_RUN_REPORT" >&2
      exit 1
      ;;
  esac
fi

if [ -n "$OUTPUT_PATH" ]; then
  ABS_OUTPUT_PATH=$(absolute_path "$OUTPUT_PATH")
  case "$ABS_OUTPUT_PATH" in
    "$ABS_ROOT"|"$ABS_ROOT"/*)
      echo "Refusing to write activation request output inside repository: $ABS_OUTPUT_PATH" >&2
      exit 1
      ;;
  esac
  mkdir -p "$(dirname "$ABS_OUTPUT_PATH")"
fi

PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" - \
  "$ABS_ROOT" \
  "$ABS_APPROVAL_GATE_REPORT" \
  "$ABS_OPERATOR_DRY_RUN_REPORT" \
  "$ABS_OUTPUT_PATH" \
  "$REQUEST_NOTE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

from stockanalysis.operations.scheduler_activation_request import (
    build_data_operations_live_scheduler_activation_request_report,
)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


repo_root = Path(sys.argv[1]).resolve()
approval_gate_report_path = Path(sys.argv[2]).resolve()
operator_dry_run_report_path_arg = sys.argv[3]
output_path = sys.argv[4]
request_note = sys.argv[5]

approval_gate_report = json.loads(approval_gate_report_path.read_text(encoding="utf-8"))
operator_report_path_value = operator_dry_run_report_path_arg or str(
    approval_gate_report.get("operator_dry_run_report_path", "")
).strip()
if not operator_report_path_value:
    raise ValueError("operator dry-run report path is required or must be recorded in the approval gate report.")

operator_dry_run_report_path = Path(operator_report_path_value).resolve()
if _is_relative_to(operator_dry_run_report_path, repo_root):
    raise ValueError(f"refusing repo-inside operator dry-run report: {operator_dry_run_report_path}")
if not operator_dry_run_report_path.is_file():
    raise ValueError(f"operator dry-run report does not exist: {operator_dry_run_report_path}")

operator_dry_run_report = json.loads(operator_dry_run_report_path.read_text(encoding="utf-8"))
evidence_paths = dict(operator_dry_run_report.get("evidence_paths", {}))
evidence_paths["operator_dry_run_report"] = str(operator_dry_run_report_path)
operator_dry_run_report["evidence_paths"] = evidence_paths

report = build_data_operations_live_scheduler_activation_request_report(
    approval_gate_report=approval_gate_report,
    operator_dry_run_report=operator_dry_run_report,
    approval_gate_report_path=str(approval_gate_report_path),
    operator_dry_run_report_path=str(operator_dry_run_report_path),
    request_note=request_note,
)
text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
if output_path:
    Path(output_path).write_text(text, encoding="utf-8")
    print(output_path)
else:
    print(text, end="")
PY
