#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
ENV_FILE=""
PYTHON_BIN="${PYTHON_BIN:-python3}"

usage() {
  cat <<'USAGE'
Usage:
  scripts/check_frontend_api_server_runtime_env.sh --env-file PATH

Checks a trusted frontend API server env file without connecting to the runtime DB.
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
    echo "Refusing to use frontend API server env file inside repository: $ABS_ENV_FILE" >&2
    exit 1
    ;;
esac

set -a
. "$ABS_ENV_FILE"
set +a

PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" - "$ABS_ENV_FILE" "$ABS_ROOT" <<'PY'
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

from stockanalysis.frontend.runtime_policy import FrontendRuntimePolicy

env_file, root_dir = sys.argv[1:]

required = [
    "STOCKANALYSIS_DATABASE_URL",
    "STOCKANALYSIS_FRONTEND_RUNTIME_PROFILE",
    "STOCKANALYSIS_FRONTEND_API_ALLOWED_ORIGIN",
    "STOCKANALYSIS_FRONTEND_API_AUTH_MODE",
    "STOCKANALYSIS_FRONTEND_API_READ_TOKEN",
    "STOCKANALYSIS_FRONTEND_API_HOST",
    "STOCKANALYSIS_FRONTEND_API_PORT",
]
placeholder_tokens = [
    "CHANGE_ME",
    "USER:PASSWORD@HOST",
    "PASSWORD",
    "HOST:5432",
    "replace-me",
    "example.invalid",
    "/absolute/path",
]

for name in required:
    value = os.environ.get(name, "")
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    if any(token in value for token in placeholder_tokens):
        raise SystemExit(f"{name} still contains a placeholder value.")

database_url = os.environ["STOCKANALYSIS_DATABASE_URL"]
parsed_db_url = urlparse(database_url)
if parsed_db_url.scheme not in {"postgresql", "postgres"}:
    raise SystemExit("STOCKANALYSIS_DATABASE_URL must use postgres/postgresql scheme.")
if not parsed_db_url.hostname or not parsed_db_url.path or parsed_db_url.path == "/":
    raise SystemExit("STOCKANALYSIS_DATABASE_URL must include host and database name.")
if parsed_db_url.username is None:
    raise SystemExit("STOCKANALYSIS_DATABASE_URL must include a database user.")

profile = os.environ["STOCKANALYSIS_FRONTEND_RUNTIME_PROFILE"]
source = os.environ.get("STOCKANALYSIS_FRONTEND_API_SOURCE", "live")
auth_mode = os.environ["STOCKANALYSIS_FRONTEND_API_AUTH_MODE"]
allowed_origin = os.environ["STOCKANALYSIS_FRONTEND_API_ALLOWED_ORIGIN"]
read_token = os.environ["STOCKANALYSIS_FRONTEND_API_READ_TOKEN"]
host = os.environ["STOCKANALYSIS_FRONTEND_API_HOST"].strip()

if profile != "production":
    raise SystemExit("STOCKANALYSIS_FRONTEND_RUNTIME_PROFILE must be production.")
if source != "live":
    raise SystemExit("STOCKANALYSIS_FRONTEND_API_SOURCE must be live for the deployment boundary.")
if auth_mode != "read-token":
    raise SystemExit("STOCKANALYSIS_FRONTEND_API_AUTH_MODE must be read-token.")
if not allowed_origin.startswith("https://") or allowed_origin == "https://cockpit.example":
    raise SystemExit("STOCKANALYSIS_FRONTEND_API_ALLOWED_ORIGIN must be an explicit HTTPS origin.")
if len(read_token) < 32:
    raise SystemExit("STOCKANALYSIS_FRONTEND_API_READ_TOKEN must be at least 32 characters.")
if host not in {"127.0.0.1", "localhost", "::1"}:
    raise SystemExit("STOCKANALYSIS_FRONTEND_API_HOST must bind loopback behind a TLS reverse proxy.")

def parse_positive_int(name: str) -> int:
    raw = os.environ.get(name, "")
    if not raw.isdigit():
        raise SystemExit(f"{name} must be a positive integer.")
    value = int(raw)
    if value <= 0:
        raise SystemExit(f"{name} must be greater than 0.")
    return value


def parse_positive_float(name: str) -> float:
    try:
        value = float(os.environ[name])
    except KeyError as exc:
        raise SystemExit(f"Missing required environment variable: {name}") from exc
    except ValueError as exc:
        raise SystemExit(f"{name} must be a positive number.") from exc
    if value <= 0:
        raise SystemExit(f"{name} must be greater than 0.")
    return value


port = parse_positive_int("STOCKANALYSIS_FRONTEND_API_PORT")
if port > 65535:
    raise SystemExit("STOCKANALYSIS_FRONTEND_API_PORT must be <= 65535.")
pool_min_size = parse_positive_int("STOCKANALYSIS_FRONTEND_API_POOL_MIN_SIZE")
pool_max_size = parse_positive_int("STOCKANALYSIS_FRONTEND_API_POOL_MAX_SIZE")
if pool_min_size > pool_max_size:
    raise SystemExit("STOCKANALYSIS_FRONTEND_API_POOL_MIN_SIZE must be <= max size.")
pool_timeout_seconds = parse_positive_float("STOCKANALYSIS_FRONTEND_API_POOL_TIMEOUT_SECONDS")
request_timeout_seconds = parse_positive_float("STOCKANALYSIS_FRONTEND_API_REQUEST_TIMEOUT_SECONDS")

repo_root = os.environ.get("STOCKANALYSIS_FRONTEND_API_REPO_ROOT", root_dir)
if not os.path.isabs(repo_root):
    raise SystemExit("STOCKANALYSIS_FRONTEND_API_REPO_ROOT must be absolute when set.")
contract_index = Path(repo_root) / "docs" / "api" / "frontend" / "contract-index.json"
if not contract_index.is_file():
    raise SystemExit("STOCKANALYSIS_FRONTEND_API_REPO_ROOT must contain docs/api/frontend/contract-index.json.")

policy = FrontendRuntimePolicy(
    profile=profile,
    source=source,
    allowed_origin=allowed_origin,
    auth_mode=auth_mode,
    read_token=read_token,
    database_url=database_url,
)
issues = policy.validation_issues(host=host)
if issues:
    raise SystemExit("; ".join(issues))

print(
    json.dumps(
        {
            "runtime_env_readiness": "passed",
            "env_file": env_file,
            "runtime_profile": profile,
            "source_mode": source,
            "bind_host": host,
            "port": port,
            "allowed_origin": allowed_origin,
            "auth_mode": auth_mode,
            "database_url_configured": True,
            "read_token_configured": True,
            "repo_root": repo_root,
            "request_timeout_seconds": request_timeout_seconds,
            "pool": {
                "min_size": pool_min_size,
                "max_size": pool_max_size,
                "timeout_seconds": pool_timeout_seconds,
            },
            "process_boundary": "loopback_api_behind_tls_reverse_proxy",
            "required_proxy_headers": ["Authorization", "X-Request-ID"],
            "public_probes": ["/__live", "/__health", "/__ready"],
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
)
PY
