#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"
ARTIFACT_ROOT=$(mktemp -d /tmp/stockanalysis-frontend-api-deployment.XXXXXX)
TEMPLATE_ENV="$ARTIFACT_ROOT/frontend-api.template.env"
VALID_ENV="$ARTIFACT_ROOT/frontend-api.valid.env"
READINESS_OUTPUT="$ARTIFACT_ROOT/readiness.json"
PREFLIGHT_OUTPUT="$ARTIFACT_ROOT/preflight.json"

cleanup() {
  rm -rf "$ARTIFACT_ROOT"
}

trap cleanup EXIT

cd "$ROOT_DIR"

bash -n scripts/render_frontend_api_server_env_template.sh
bash -n scripts/check_frontend_api_server_runtime_env.sh
bash -n scripts/run_frontend_api_server.sh
bash -n scripts/verify_frontend_api_server_deployment_boundary.sh

if scripts/render_frontend_api_server_env_template.sh --output "$ROOT_DIR/frontend-api.env" >/dev/null 2>&1; then
  echo "renderer accepted a repo-internal output path" >&2
  exit 1
fi

scripts/render_frontend_api_server_env_template.sh --output "$TEMPLATE_ENV" >/dev/null

if PYTHON_BIN="$PYTHON_BIN" scripts/check_frontend_api_server_runtime_env.sh --env-file "$TEMPLATE_ENV" >/dev/null 2>&1; then
  echo "readiness check accepted an unedited template" >&2
  exit 1
fi

cat > "$VALID_ENV" <<ENV
STOCKANALYSIS_DATABASE_URL="postgresql://stockanalysis_app:runtime_password@db.stockanalysis.internal:5432/stockanalysis"
STOCKANALYSIS_FRONTEND_RUNTIME_PROFILE="production"
STOCKANALYSIS_FRONTEND_API_ALLOWED_ORIGIN="https://cockpit.stockanalysis.internal"
STOCKANALYSIS_FRONTEND_API_AUTH_MODE="read-token"
STOCKANALYSIS_FRONTEND_API_READ_TOKEN="valid-read-token-000000000000000000000"
STOCKANALYSIS_FRONTEND_API_REQUEST_TIMEOUT_SECONDS="30"
STOCKANALYSIS_FRONTEND_API_HOST="127.0.0.1"
STOCKANALYSIS_FRONTEND_API_PORT="8787"
STOCKANALYSIS_FRONTEND_API_SOURCE="live"
STOCKANALYSIS_FRONTEND_API_REPO_ROOT="$ROOT_DIR"
STOCKANALYSIS_FRONTEND_API_POOL_MIN_SIZE="1"
STOCKANALYSIS_FRONTEND_API_POOL_MAX_SIZE="4"
STOCKANALYSIS_FRONTEND_API_POOL_TIMEOUT_SECONDS="10"
ENV

chmod 600 "$VALID_ENV"

PYTHON_BIN="$PYTHON_BIN" scripts/check_frontend_api_server_runtime_env.sh --env-file "$VALID_ENV" > "$READINESS_OUTPUT"
PYTHON_BIN="$PYTHON_BIN" scripts/run_frontend_api_server.sh --env-file "$VALID_ENV" --preflight-only > "$PREFLIGHT_OUTPUT"

"$PYTHON_BIN" - "$READINESS_OUTPUT" "$PREFLIGHT_OUTPUT" "$VALID_ENV" "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

readiness_path, preflight_path, env_file, root_dir = sys.argv[1:]

readiness = json.loads(Path(readiness_path).read_text(encoding="utf-8"))
preflight = json.loads(Path(preflight_path).read_text(encoding="utf-8"))

for payload in [readiness, preflight]:
    assert payload["runtime_env_readiness"] == "passed", payload
    assert payload["env_file"] == env_file, payload
    assert payload["runtime_profile"] == "production", payload
    assert payload["source_mode"] == "live", payload
    assert payload["bind_host"] == "127.0.0.1", payload
    assert payload["port"] == 8787, payload
    assert payload["allowed_origin"] == "https://cockpit.stockanalysis.internal", payload
    assert payload["database_url_configured"] is True, payload
    assert payload["read_token_configured"] is True, payload
    assert payload["repo_root"] == root_dir, payload
    assert payload["process_boundary"] == "loopback_api_behind_tls_reverse_proxy", payload
    assert "/__ready" in payload["public_probes"], payload
    serialized = json.dumps(payload)
    assert "runtime_password" not in serialized, payload
    assert "valid-read-token" not in serialized, payload
    assert "postgresql://" not in serialized, payload

assert readiness == preflight, (readiness, preflight)
PY

echo "frontend API server deployment boundary verification passed"
