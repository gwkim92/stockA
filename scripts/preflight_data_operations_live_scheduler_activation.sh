#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

ACTIVATION_DECISION_REPORT=""
ACTIVATION_REQUEST_REPORT=""
APPROVAL_GATE_REPORT=""
OPERATOR_DRY_RUN_REPORT=""
ENV_FILE=""
OUTPUT_DIR=""
PYTHON_BIN="${PYTHON_BIN:-python3}"

usage() {
  cat <<'USAGE'
Usage:
  scripts/preflight_data_operations_live_scheduler_activation.sh --activation-decision-report PATH --env-file PATH --output-dir PATH [options]

Options:
  --activation-request-report PATH  Repo-outside activation request JSON. Defaults to the path recorded in the decision report.
  --approval-gate-report PATH       Repo-outside approval gate JSON. Defaults to the path recorded in the request report.
  --operator-dry-run-report PATH    Repo-outside operator dry-run JSON. Defaults to the path recorded in the request report.

Runs final preflight for live scheduler activation by re-checking runtime env
readiness and validating the activation evidence chain. It never runs launchctl
and never writes LaunchAgents.
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
    --activation-decision-report)
      if [ "$#" -lt 2 ]; then
        echo "--activation-decision-report requires a path." >&2
        exit 2
      fi
      ACTIVATION_DECISION_REPORT="$2"
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
    --env-file)
      if [ "$#" -lt 2 ]; then
        echo "--env-file requires a path." >&2
        exit 2
      fi
      ENV_FILE="$2"
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

if [ -z "$ACTIVATION_DECISION_REPORT" ]; then
  echo "Missing required --activation-decision-report PATH." >&2
  exit 1
fi
if [ -z "$ENV_FILE" ]; then
  echo "Missing required --env-file PATH." >&2
  exit 1
fi
if [ -z "$OUTPUT_DIR" ]; then
  echo "Missing required --output-dir PATH." >&2
  exit 1
fi
if [ ! -f "$ACTIVATION_DECISION_REPORT" ]; then
  echo "Activation decision report does not exist: $ACTIVATION_DECISION_REPORT" >&2
  exit 1
fi
if [ ! -f "$ENV_FILE" ]; then
  echo "Env file does not exist: $ENV_FILE" >&2
  exit 1
fi

ABS_ROOT=$(absolute_path "$ROOT_DIR")
ABS_ACTIVATION_DECISION_REPORT=$(absolute_path "$ACTIVATION_DECISION_REPORT")
ABS_ENV_FILE=$(absolute_path "$ENV_FILE")
ABS_OUTPUT_DIR=$(absolute_path "$OUTPUT_DIR")
ABS_ACTIVATION_REQUEST_REPORT=""
ABS_APPROVAL_GATE_REPORT=""
ABS_OPERATOR_DRY_RUN_REPORT=""

case "$ABS_ACTIVATION_DECISION_REPORT" in
  "$ABS_ROOT"|"$ABS_ROOT"/*)
    echo "Refusing to use activation decision report inside repository: $ABS_ACTIVATION_DECISION_REPORT" >&2
    exit 1
    ;;
esac
case "$ABS_ENV_FILE" in
  "$ABS_ROOT"|"$ABS_ROOT"/*)
    echo "Refusing to use data operations env file inside repository: $ABS_ENV_FILE" >&2
    exit 1
    ;;
esac
case "$ABS_OUTPUT_DIR" in
  "$ABS_ROOT"|"$ABS_ROOT"/*)
    echo "Refusing to write final preflight output inside repository: $ABS_OUTPUT_DIR" >&2
    exit 1
    ;;
esac

if [ -n "$ACTIVATION_REQUEST_REPORT" ]; then
  ABS_ACTIVATION_REQUEST_REPORT=$(absolute_path "$ACTIVATION_REQUEST_REPORT")
fi
if [ -n "$APPROVAL_GATE_REPORT" ]; then
  ABS_APPROVAL_GATE_REPORT=$(absolute_path "$APPROVAL_GATE_REPORT")
fi
if [ -n "$OPERATOR_DRY_RUN_REPORT" ]; then
  ABS_OPERATOR_DRY_RUN_REPORT=$(absolute_path "$OPERATOR_DRY_RUN_REPORT")
fi

mkdir -p "$ABS_OUTPUT_DIR/evidence"
RUNTIME_READINESS_REPORT="$ABS_OUTPUT_DIR/evidence/fresh-runtime-env-readiness.json"
FINAL_PREFLIGHT_REPORT="$ABS_OUTPUT_DIR/final-preflight.json"

set -a
. "$ABS_ENV_FILE"
set +a

PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" - \
  "$ABS_ROOT" \
  "$ABS_ENV_FILE" \
  "$RUNTIME_READINESS_REPORT" \
  "$ABS_ACTIVATION_DECISION_REPORT" \
  "$ABS_ACTIVATION_REQUEST_REPORT" \
  "$ABS_APPROVAL_GATE_REPORT" \
  "$ABS_OPERATOR_DRY_RUN_REPORT" \
  "$FINAL_PREFLIGHT_REPORT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

from stockanalysis.operations.env_readiness import check_data_operations_runtime_env
from stockanalysis.operations.scheduler_activation_final_preflight import (
    build_data_operations_live_scheduler_activation_final_preflight_report,
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
env_file = Path(sys.argv[2]).resolve()
runtime_readiness_report_path = Path(sys.argv[3]).resolve()
decision_report_path = _repo_outside_existing_file(sys.argv[4], repo_root, "activation decision report")
request_report_path_arg = sys.argv[5]
approval_gate_report_path_arg = sys.argv[6]
operator_dry_run_report_path_arg = sys.argv[7]
final_preflight_report_path = Path(sys.argv[8]).resolve()

runtime_readiness = check_data_operations_runtime_env(
    repo_root=repo_root,
    env_file=env_file,
    strict=False,
)
runtime_readiness_report_path.write_text(
    json.dumps(runtime_readiness, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
    encoding="utf-8",
)

decision_report = json.loads(decision_report_path.read_text(encoding="utf-8"))
request_report_path_value = request_report_path_arg or str(
    decision_report.get("activation_request_report_path", "")
).strip()
if not request_report_path_value:
    raise ValueError("activation request report path is required or must be recorded in the decision report.")
request_report_path = _repo_outside_existing_file(request_report_path_value, repo_root, "activation request report")
request_report = json.loads(request_report_path.read_text(encoding="utf-8"))

approval_gate_report_path_value = approval_gate_report_path_arg or str(
    request_report.get("approval_gate_report_path", "")
).strip()
if not approval_gate_report_path_value:
    raise ValueError("approval gate report path is required or must be recorded in the activation request report.")
approval_gate_report_path = _repo_outside_existing_file(approval_gate_report_path_value, repo_root, "approval gate report")
approval_gate_report = json.loads(approval_gate_report_path.read_text(encoding="utf-8"))

operator_report_path_value = operator_dry_run_report_path_arg or str(
    request_report.get("operator_dry_run_report_path", "")
).strip()
if not operator_report_path_value:
    raise ValueError("operator dry-run report path is required or must be recorded in the activation request report.")
operator_report_path = _repo_outside_existing_file(operator_report_path_value, repo_root, "operator dry-run report")
operator_report = json.loads(operator_report_path.read_text(encoding="utf-8"))

report = build_data_operations_live_scheduler_activation_final_preflight_report(
    activation_decision_report=decision_report,
    activation_request_report=request_report,
    approval_gate_report=approval_gate_report,
    operator_dry_run_report=operator_report,
    runtime_env_readiness_report=runtime_readiness,
    activation_decision_report_path=str(decision_report_path),
    activation_request_report_path=str(request_report_path),
    approval_gate_report_path=str(approval_gate_report_path),
    operator_dry_run_report_path=str(operator_report_path),
    runtime_env_readiness_report_path=str(runtime_readiness_report_path),
)
final_preflight_report_path.write_text(
    json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(final_preflight_report_path)
PY
