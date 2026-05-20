#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
OUTPUT_DIR=""
ENV_FILE=""
JOB_ID=""
LABEL=""
TIMEOUT_SECONDS="3600"
PYTHON_BIN="${PYTHON_BIN:-python3}"
COMMAND=()

usage() {
  cat <<'USAGE'
Usage:
  scripts/render_data_operations_scheduler_install.sh --output-dir PATH --env-file PATH --job-id JOB_ID [options] -- COMMAND...

Options:
  --label LABEL          Optional launchd label. Defaults to com.stockanalysis.data-operations.<job-id>.
  --timeout-seconds N   Timeout passed to run_data_operations_scheduler_job.sh. Default: 3600.

Renders launchd dry-run artifacts only. It does not write to host scheduler
directories and does not install or activate launchd.
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
    --output-dir)
      if [ "$#" -lt 2 ]; then
        echo "--output-dir requires a path." >&2
        exit 2
      fi
      OUTPUT_DIR="$2"
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
    --job-id)
      if [ "$#" -lt 2 ]; then
        echo "--job-id requires a value." >&2
        exit 2
      fi
      JOB_ID="$2"
      shift 2
      ;;
    --label)
      if [ "$#" -lt 2 ]; then
        echo "--label requires a value." >&2
        exit 2
      fi
      LABEL="$2"
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

if [ -z "$OUTPUT_DIR" ]; then
  echo "Missing required --output-dir PATH." >&2
  exit 1
fi

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

WRAPPER_PATH="$ROOT_DIR/scripts/run_data_operations_scheduler_job.sh"
if [ ! -x "$WRAPPER_PATH" ]; then
  echo "Scheduler wrapper is missing or not executable: $WRAPPER_PATH" >&2
  exit 1
fi

ABS_ROOT=$(absolute_path "$ROOT_DIR")
ABS_OUTPUT_DIR=$(absolute_path "$OUTPUT_DIR")
ABS_ENV_FILE=$(absolute_path "$ENV_FILE")
ABS_WRAPPER_PATH=$(absolute_path "$WRAPPER_PATH")

case "$ABS_OUTPUT_DIR" in
  "$ABS_ROOT"|"$ABS_ROOT"/*)
    echo "Refusing to render data operations scheduler install artifacts inside repository: $ABS_OUTPUT_DIR" >&2
    exit 1
    ;;
esac

case "$ABS_ENV_FILE" in
  "$ABS_ROOT"|"$ABS_ROOT"/*)
    echo "Refusing to use data operations scheduler env file inside repository: $ABS_ENV_FILE" >&2
    exit 1
    ;;
esac

mkdir -p "$ABS_OUTPUT_DIR"

PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" - "$ABS_ROOT" "$ABS_OUTPUT_DIR" "$ABS_ENV_FILE" "$JOB_ID" "$LABEL" "$TIMEOUT_SECONDS" "$ABS_WRAPPER_PATH" "${COMMAND[@]}" <<'PY'
from __future__ import annotations

import json
import os
import plistlib
import sys
from pathlib import Path

from stockanalysis.operations.scheduler_install import (
    build_data_operations_launchd_plist,
    build_data_operations_scheduler_install_manifest,
    default_launchd_label,
)

repo_root, output_dir, env_file, job_id, label, timeout_seconds, wrapper_path, *command = sys.argv[1:]
label_value = label or default_launchd_label(job_id)
plist_path = Path(output_dir) / f"{label_value}.plist"
manifest_path = Path(output_dir) / f"{label_value}.manifest.json"

plist_payload = build_data_operations_launchd_plist(
    job_id=job_id,
    repo_root=repo_root,
    env_file=env_file,
    wrapper_path=wrapper_path,
    output_dir=output_dir,
    command_argv=command,
    label=label_value,
    timeout_seconds=int(timeout_seconds),
)
manifest = build_data_operations_scheduler_install_manifest(
    job_id=job_id,
    label=label_value,
    plist_path=plist_path,
    env_file=env_file,
    wrapper_path=wrapper_path,
    output_dir=output_dir,
    command_argv=command,
    timeout_seconds=int(timeout_seconds),
)
manifest["manifest_path"] = str(manifest_path)

with open(plist_path, "wb") as handle:
    plistlib.dump(plist_payload, handle, sort_keys=False)
with open(manifest_path, "w", encoding="utf-8") as handle:
    json.dump(manifest, handle, indent=2, ensure_ascii=False, sort_keys=True)
    handle.write("\n")
os.chmod(plist_path, 0o600)
os.chmod(manifest_path, 0o600)
print(manifest_path)
PY
