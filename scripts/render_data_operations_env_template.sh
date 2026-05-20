#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
OUTPUT_PATH=""
FORCE="false"
PYTHON_BIN="${PYTHON_BIN:-python3}"

usage() {
  cat <<'USAGE'
Usage:
  scripts/render_data_operations_env_template.sh --output PATH [--force]

Renders a data operations runtime env template to a repo-outside path.
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
    --output)
      if [ "$#" -lt 2 ]; then
        echo "--output requires a path." >&2
        exit 2
      fi
      OUTPUT_PATH="$2"
      shift 2
      ;;
    --force)
      FORCE="true"
      shift
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

if [ -z "$OUTPUT_PATH" ]; then
  echo "Missing required --output PATH." >&2
  exit 1
fi

ABS_ROOT=$(absolute_path "$ROOT_DIR")
ABS_OUTPUT=$(absolute_path "$OUTPUT_PATH")

case "$ABS_OUTPUT" in
  "$ABS_ROOT"|"$ABS_ROOT"/*)
    echo "Refusing to render data operations env template inside repository: $ABS_OUTPUT" >&2
    exit 1
    ;;
esac

if [ -e "$ABS_OUTPUT" ] && [ "$FORCE" != "true" ]; then
  echo "Output already exists. Use --force to overwrite: $ABS_OUTPUT" >&2
  exit 1
fi

mkdir -p "$(dirname "$ABS_OUTPUT")"
PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" - > "$ABS_OUTPUT" <<'PY'
from stockanalysis.operations.env_readiness import render_data_operations_env_template

print(render_data_operations_env_template())
PY
chmod 600 "$ABS_OUTPUT"
echo "$ABS_OUTPUT"
