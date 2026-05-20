#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
ENV_FILE=""
PYTHON_BIN="${PYTHON_BIN:-python3}"

usage() {
  cat <<'USAGE'
Usage:
  scripts/check_data_operations_runtime_env.sh --env-file PATH

Checks a trusted data operations env file without connecting to external providers.
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

if [ -z "$ENV_FILE" ]; then
  echo "Missing required --env-file PATH." >&2
  exit 1
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

set -a
. "$ABS_ENV_FILE"
set +a

PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m stockanalysis.ingest.cli \
  data-operations-env-readiness \
  --env-file "$ABS_ENV_FILE" \
  --repo-root "$ABS_ROOT"
