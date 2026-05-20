#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

FINAL_PREFLIGHT_REPORT=""
ACTIVATION_REQUEST_REPORT=""
OUTPUT_DIR=""
PYTHON_BIN="${PYTHON_BIN:-python3}"

usage() {
  cat <<'USAGE'
Usage:
  scripts/plan_data_operations_live_scheduler_host_activation.sh --final-preflight-report PATH --output-dir PATH [options]

Options:
  --activation-request-report PATH  Repo-outside activation request JSON. Defaults to the path recorded in the final preflight report.

Creates a host activation plan and command preview for operator review. It never
runs launchctl and never writes LaunchAgents.
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
    --final-preflight-report)
      if [ "$#" -lt 2 ]; then
        echo "--final-preflight-report requires a path." >&2
        exit 2
      fi
      FINAL_PREFLIGHT_REPORT="$2"
      shift 2
      ;;
    --activation-request-report)
      if [ "$#" -lt 2 ]; then
        echo "--activation-request-report requires a path." >&2
        exit 2
      fi
      ACTIVATION_REQUEST_REPORT="$2"
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

if [ -z "$FINAL_PREFLIGHT_REPORT" ]; then
  echo "Missing required --final-preflight-report PATH." >&2
  exit 1
fi
if [ -z "$OUTPUT_DIR" ]; then
  echo "Missing required --output-dir PATH." >&2
  exit 1
fi
if [ ! -f "$FINAL_PREFLIGHT_REPORT" ]; then
  echo "Final preflight report does not exist: $FINAL_PREFLIGHT_REPORT" >&2
  exit 1
fi

ABS_ROOT=$(absolute_path "$ROOT_DIR")
ABS_FINAL_PREFLIGHT_REPORT=$(absolute_path "$FINAL_PREFLIGHT_REPORT")
ABS_ACTIVATION_REQUEST_REPORT=""
ABS_OUTPUT_DIR=$(absolute_path "$OUTPUT_DIR")

case "$ABS_FINAL_PREFLIGHT_REPORT" in
  "$ABS_ROOT"|"$ABS_ROOT"/*)
    echo "Refusing to use final preflight report inside repository: $ABS_FINAL_PREFLIGHT_REPORT" >&2
    exit 1
    ;;
esac
case "$ABS_OUTPUT_DIR" in
  "$ABS_ROOT"|"$ABS_ROOT"/*)
    echo "Refusing to write host activation plan output inside repository: $ABS_OUTPUT_DIR" >&2
    exit 1
    ;;
esac

if [ -n "$ACTIVATION_REQUEST_REPORT" ]; then
  if [ ! -f "$ACTIVATION_REQUEST_REPORT" ]; then
    echo "Activation request report does not exist: $ACTIVATION_REQUEST_REPORT" >&2
    exit 1
  fi
  ABS_ACTIVATION_REQUEST_REPORT=$(absolute_path "$ACTIVATION_REQUEST_REPORT")
  case "$ABS_ACTIVATION_REQUEST_REPORT" in
    "$ABS_ROOT"|"$ABS_ROOT"/*)
      echo "Refusing to use activation request report inside repository: $ABS_ACTIVATION_REQUEST_REPORT" >&2
      exit 1
      ;;
  esac
fi

mkdir -p "$ABS_OUTPUT_DIR"
PLAN_JSON="$ABS_OUTPUT_DIR/host-activation-plan.json"
PLAN_MARKDOWN="$ABS_OUTPUT_DIR/host-activation-plan.md"

PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" - \
  "$ABS_ROOT" \
  "$ABS_FINAL_PREFLIGHT_REPORT" \
  "$ABS_ACTIVATION_REQUEST_REPORT" \
  "$PLAN_JSON" \
  "$PLAN_MARKDOWN" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

from stockanalysis.operations.scheduler_activation_host_plan import (
    build_data_operations_live_scheduler_host_activation_plan_report,
    render_data_operations_live_scheduler_host_activation_plan_markdown,
)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _repo_outside_existing_file(value: str, root: Path, label: str) -> Path:
    path = Path(value).resolve()
    if _is_relative_to(path, root):
        raise ValueError(f"refusing repo-inside {label}: {path}")
    if not path.is_file():
        raise ValueError(f"{label} does not exist: {path}")
    return path


repo_root = Path(sys.argv[1]).resolve()
final_preflight_report_path = _repo_outside_existing_file(sys.argv[2], repo_root, "final preflight report")
activation_request_report_arg = sys.argv[3]
plan_json_path = Path(sys.argv[4]).resolve()
plan_markdown_path = Path(sys.argv[5]).resolve()

final_preflight = json.loads(final_preflight_report_path.read_text(encoding="utf-8"))
request_report_path_value = activation_request_report_arg or str(
    final_preflight.get("activation_request_report_path", "")
).strip()
if not request_report_path_value:
    raise ValueError("activation request report path is required or must be recorded in the final preflight report.")
activation_request_report_path = _repo_outside_existing_file(
    request_report_path_value,
    repo_root,
    "activation request report",
)
activation_request = json.loads(activation_request_report_path.read_text(encoding="utf-8"))

report = build_data_operations_live_scheduler_host_activation_plan_report(
    final_preflight_report=final_preflight,
    activation_request_report=activation_request,
    final_preflight_report_path=str(final_preflight_report_path),
    activation_request_report_path=str(activation_request_report_path),
)
text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
plan_json_path.write_text(text, encoding="utf-8")
plan_markdown_path.write_text(
    render_data_operations_live_scheduler_host_activation_plan_markdown(report),
    encoding="utf-8",
)
print(plan_json_path)
PY
