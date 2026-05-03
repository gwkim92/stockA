#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
ENV_FILE=""
PREFLIGHT_ONLY="false"
PYTHON_BIN="${PYTHON_BIN:-python3}"

usage() {
  cat <<'USAGE'
Usage:
  scripts/run_frontend_api_server.sh --env-file PATH [--preflight-only]

Runs the FastAPI read-only frontend API server from a repo-outside env file.
USAGE
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
    --preflight-only)
      PREFLIGHT_ONLY="true"
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

if [ -z "$ENV_FILE" ]; then
  echo "Missing required --env-file PATH." >&2
  exit 1
fi

PYTHON_BIN="$PYTHON_BIN" "$ROOT_DIR/scripts/check_frontend_api_server_runtime_env.sh" --env-file "$ENV_FILE"

if [ "$PREFLIGHT_ONLY" = "true" ]; then
  exit 0
fi

set -a
. "$ENV_FILE"
set +a

ARGS=(
  -m stockanalysis.frontend.api_server
  --host "$STOCKANALYSIS_FRONTEND_API_HOST"
  --port "$STOCKANALYSIS_FRONTEND_API_PORT"
  --source "${STOCKANALYSIS_FRONTEND_API_SOURCE:-live}"
  --runtime-profile "$STOCKANALYSIS_FRONTEND_RUNTIME_PROFILE"
  --allowed-origin "$STOCKANALYSIS_FRONTEND_API_ALLOWED_ORIGIN"
  --auth-mode "$STOCKANALYSIS_FRONTEND_API_AUTH_MODE"
  --pool-min-size "$STOCKANALYSIS_FRONTEND_API_POOL_MIN_SIZE"
  --pool-max-size "$STOCKANALYSIS_FRONTEND_API_POOL_MAX_SIZE"
  --pool-timeout-seconds "$STOCKANALYSIS_FRONTEND_API_POOL_TIMEOUT_SECONDS"
  --request-timeout-seconds "$STOCKANALYSIS_FRONTEND_API_REQUEST_TIMEOUT_SECONDS"
)

if [ -n "${STOCKANALYSIS_FRONTEND_API_REPO_ROOT:-}" ]; then
  ARGS+=(--repo-root "$STOCKANALYSIS_FRONTEND_API_REPO_ROOT")
fi

cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$PYTHON_BIN" "${ARGS[@]}"
