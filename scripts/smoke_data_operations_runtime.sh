#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"
ENV_FILE=""
JOB_ID="macro-weekly"
TIMEOUT_SECONDS="3600"
PYTHON_BIN="${PYTHON_BIN:-python3}"

usage() {
  cat <<'USAGE'
Usage:
  scripts/smoke_data_operations_runtime.sh --env-file PATH [--job-id JOB_ID] [--timeout-seconds N] -- COMMAND...

Runs data operations env readiness, then executes COMMAND through data-operations-run.
The env file must be trusted and stored outside the repository.
USAGE
}

absolute_path() {
  python3 - "$1" <<'PY'
import os
import sys

print(os.path.abspath(sys.argv[1]))
PY
}

COMMAND=()
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
    echo "Refusing to use data operations env file inside repository: $ABS_ENV_FILE" >&2
    exit 1
    ;;
esac

TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/stockanalysis-data-ops-runtime-smoke.XXXXXX")
trap 'rm -rf "$TMP_DIR"' EXIT

READINESS_JSON="$TMP_DIR/readiness.json"
ARTIFACT_RUN_JSON="$TMP_DIR/artifact-run.json"

scripts/check_data_operations_runtime_env.sh --env-file "$ABS_ENV_FILE" > "$READINESS_JSON"

set -a
. "$ABS_ENV_FILE"
set +a

if [ -z "${STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT:-}" ]; then
  echo "Missing required environment variable: STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT" >&2
  exit 1
fi

set +e
PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m stockanalysis.ingest.cli \
  data-operations-run \
  --job-id "$JOB_ID" \
  --artifact-root "$STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT" \
  --timeout-seconds "$TIMEOUT_SECONDS" \
  -- "${COMMAND[@]}" > "$ARTIFACT_RUN_JSON"
RUN_EXIT_CODE=$?
set -e

PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" - "$READINESS_JSON" "$ARTIFACT_RUN_JSON" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

from stockanalysis.operations.runtime_smoke import build_data_operations_runtime_smoke_report

readiness_path, artifact_run_path = sys.argv[1:]
readiness = json.loads(Path(readiness_path).read_text(encoding="utf-8"))
artifact_run = json.loads(Path(artifact_run_path).read_text(encoding="utf-8"))
report = build_data_operations_runtime_smoke_report(
    readiness_report=readiness,
    artifact_run=artifact_run,
)
print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
PY

exit "$RUN_EXIT_CODE"
