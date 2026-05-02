#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
ARTIFACT_ROOT=$(mktemp -d /tmp/stockanalysis-frontend-runtime-boundary.XXXXXX)

cleanup() {
  rm -rf "$ARTIFACT_ROOT"
}

trap cleanup EXIT

cd "$ROOT_DIR"

bash -n scripts/verify_frontend_api_runtime_boundary.sh
python3 -m compileall src tests >/dev/null
PYTHONPATH=src python3 -m unittest tests.test_frontend_fixture_server -v
bash scripts/verify_frontend_fixture_server.sh

PYTHONPATH=src python3 - "$ARTIFACT_ROOT" <<'PY'
from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from stockanalysis.frontend.fixture_server import create_frontend_fixture_server

artifact_root = Path(sys.argv[1])


def start_server(**kwargs: Any):
    server = create_frontend_fixture_server(port=0, **kwargs)
    host, port = server.server_address
    base_url = f"http://{host}:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, base_url


def fetch_json(base_url: str, path: str, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    request = Request(f"{base_url}{path}", headers=headers or {})
    with urlopen(request, timeout=5) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def fetch_error_json(base_url: str, path: str, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    request = Request(f"{base_url}{path}", headers=headers or {})
    try:
        urlopen(request, timeout=5)
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))
    raise AssertionError(f"{path} unexpectedly succeeded")


try:
    create_frontend_fixture_server(
        host="0.0.0.0",
        port=0,
        source="fixture",
        runtime_profile="local",
        auth_mode="disabled",
        allowed_origin="*",
    )
except ValueError:
    pass
else:
    raise AssertionError("non-loopback unauthenticated local runtime unexpectedly started")

os.environ["STOCKANALYSIS_FRONTEND_API_READ_TOKEN"] = "runtime-secret"
token_server, token_thread, token_base_url = start_server(
    source="fixture",
    runtime_profile="local",
    allowed_origin="*",
    auth_mode="read-token",
)
try:
    status, health = fetch_json(token_base_url, "/__health")
    assert status == 200, health
    assert health["runtime"]["read_auth_required"] is True, health

    status, unauthorized = fetch_error_json(token_base_url, "/api/dashboard/today")
    assert status == 401, unauthorized
    assert unauthorized["error"]["code"] == "Unauthorized", unauthorized

    status, dashboard = fetch_json(
        token_base_url,
        "/api/dashboard/today",
        headers={"Authorization": "Bearer runtime-secret"},
    )
    assert status == 200, dashboard
    assert dashboard["data"]["portfolio_name"] == "Long Term Paper", dashboard
finally:
    token_server.shutdown()
    token_server.server_close()
    token_thread.join(timeout=5)

try:
    create_frontend_fixture_server(source="fixture", runtime_profile="production", auth_mode="disabled")
except ValueError:
    pass
else:
    raise AssertionError("unguarded production fixture runtime unexpectedly started")

os.environ["STOCKANALYSIS_PSQL_COMMAND"] = "psql postgresql://example.invalid/db"
prod_server, prod_thread, prod_base_url = start_server(
    source="auto",
    runtime_profile="production",
    allowed_origin="https://cockpit.example",
    auth_mode="read-token",
)
try:
    status, health = fetch_json(prod_base_url, "/__health")
    assert status == 200, health
    assert health["runtime"]["runtime_profile"] == "production", health
    assert health["runtime"]["source_mode"] == "auto", health
    assert health["runtime"]["allowed_origin"] == "https://cockpit.example", health
finally:
    prod_server.shutdown()
    prod_server.server_close()
    prod_thread.join(timeout=5)

summary = {
    "status": "passed",
    "checked_boundaries": [
        "local_non_loopback_guard",
        "read_token_auth_guard",
        "production_startup_guard",
        "production_metadata",
    ],
}
(artifact_root / "runtime-boundary-smoke.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
PY

echo "frontend API runtime boundary verification passed"
