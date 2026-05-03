#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
OUTPUT_PATH=""
FORCE="false"

usage() {
  cat <<'USAGE'
Usage:
  scripts/render_frontend_api_server_env_template.sh --output PATH [--force]

Renders a FastAPI frontend API server env template to a repo-outside path.
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
    echo "Refusing to render frontend API server env template inside repository: $ABS_OUTPUT" >&2
    exit 1
    ;;
esac

if [ -e "$ABS_OUTPUT" ] && [ "$FORCE" != "true" ]; then
  echo "Output already exists. Use --force to overwrite: $ABS_OUTPUT" >&2
  exit 1
fi

mkdir -p "$(dirname "$ABS_OUTPUT")"

cat > "$ABS_OUTPUT" <<ENV
# Stockanalysis frontend API server env.
# This file is sourced as shell by scripts/run_frontend_api_server.sh.
# Keep it outside the repository and do not commit credentials.

STOCKANALYSIS_DATABASE_URL="postgresql://USER:PASSWORD@HOST:5432/stockanalysis"
STOCKANALYSIS_FRONTEND_RUNTIME_PROFILE="production"
STOCKANALYSIS_FRONTEND_API_ALLOWED_ORIGIN="https://cockpit.example"
STOCKANALYSIS_FRONTEND_API_AUTH_MODE="read-token"
STOCKANALYSIS_FRONTEND_API_READ_TOKEN="CHANGE_ME_LONG_RANDOM_READ_TOKEN_AT_LEAST_32_CHARS"
STOCKANALYSIS_FRONTEND_API_REQUEST_TIMEOUT_SECONDS="30"

# Process boundary.
# Keep the API server on loopback and expose it through a TLS reverse proxy.
STOCKANALYSIS_FRONTEND_API_HOST="127.0.0.1"
STOCKANALYSIS_FRONTEND_API_PORT="8787"
STOCKANALYSIS_FRONTEND_API_SOURCE="live"
STOCKANALYSIS_FRONTEND_API_REPO_ROOT="$ROOT_DIR"

# psycopg pool boundary.
STOCKANALYSIS_FRONTEND_API_POOL_MIN_SIZE="1"
STOCKANALYSIS_FRONTEND_API_POOL_MAX_SIZE="4"
STOCKANALYSIS_FRONTEND_API_POOL_TIMEOUT_SECONDS="10"
ENV

chmod 600 "$ABS_OUTPUT"
echo "$ABS_OUTPUT"
