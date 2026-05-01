#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
ARTIFACT_ROOT=$(mktemp -d /tmp/stockanalysis-frontend-fixture-server.XXXXXX)

cleanup() {
  rm -rf "$ARTIFACT_ROOT"
}

trap cleanup EXIT

cd "$ROOT_DIR"

bash -n scripts/verify_frontend_fixture_server.sh
python3 -m compileall src tests >/dev/null
PYTHONPATH=src python3 -m unittest tests.test_frontend_fixture_server -v
bash scripts/verify_frontend_api_adapter.sh
PYTHONPATH=src python3 -m stockanalysis.frontend.fixture_server --help >/dev/null

PYTHONPATH=src python3 - "$ARTIFACT_ROOT" <<'PY'
from __future__ import annotations

import json
import sys
import threading
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from stockanalysis.frontend.fixture_server import create_frontend_fixture_server

artifact_root = Path(sys.argv[1])
server = create_frontend_fixture_server(port=0)
host, port = server.server_address
base_url = f"http://{host}:{port}"
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()


def fetch_json(path: str) -> tuple[int, dict[str, Any]]:
    with urlopen(f"{base_url}{path}", timeout=5) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def fetch_error_json(path: str, method: str = "GET") -> tuple[int, dict[str, Any]]:
    request = Request(f"{base_url}{path}", method=method)
    if method not in {"GET", "HEAD"}:
        request.data = b"{}"
    try:
        urlopen(request, timeout=5)
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))
    raise AssertionError(f"{method} {path} unexpectedly succeeded")


try:
    status, health = fetch_json("/__health")
    assert status == 200, health
    assert health["contract_version"] == "frontend-api-v0.1", health
    assert health["endpoint_count"] == 12, health
    assert health["source_mode"] == "fixture", health

    status, endpoints = fetch_json("/__endpoints")
    assert status == 200, endpoints
    assert len(endpoints["data"]["endpoints"]) == 12, endpoints
    assert endpoints["source_mode"] == "fixture", endpoints

    status, dashboard = fetch_json("/api/dashboard/today")
    assert status == 200, dashboard
    assert dashboard["data"]["portfolio_name"] == "Long Term Paper", dashboard
    assert dashboard["data"]["attention_summary"]["open_ticket_count"] == 1, dashboard

    status, tickets = fetch_json("/api/remediation-tickets?status=open")
    assert status == 200, tickets
    assert tickets["data"]["tickets"][0]["symbol"] == "BABA", tickets

    status, ai_evidence = fetch_json("/api/ai-evidence/sec-event-aapl-10k-20240928")
    assert status == 200, ai_evidence
    assert ai_evidence["data"]["source_document_id"] == "aapl-2024-10k-20240928", ai_evidence

    status, source_document = fetch_json("/api/source-documents/aapl-2024-10k-20240928")
    assert status == 200, source_document
    assert source_document["data"]["linked_evidence"][0]["evidence_id"] == "sec-event-aapl-10k-20240928", source_document

    status, events = fetch_json("/api/events?asOfDate=2024-11-01")
    assert status == 200, events
    assert events["data"]["summary"]["event_count"] == 2, events
    assert events["data"]["events"][0]["ai_evidence_id"] == "sec-event-aapl-10k-20240928", events

    status, theme = fetch_json("/api/themes/ANNUAL_REPORTING?asOfDate=2024-11-01")
    assert status == 200, theme
    assert theme["data"]["theme_key"] == "ANNUAL_REPORTING", theme
    assert theme["data"]["linked_instruments"][0]["symbol"] == "AAPL", theme

    status, performance = fetch_json("/api/performance/Long%20Term%20Paper/outcomes?measurementEndDate=2024-12-02")
    assert status == 200, performance
    assert performance["data"]["summary"]["measured_recommendation_count"] == 1, performance
    assert performance["data"]["outcomes"][0]["recommendation_id"] == "AAPL-2024-11-01", performance
    assert performance["data"]["coverage_exclusions"][0]["symbol"] == "BABA", performance

    status, not_found = fetch_error_json("/api/not-found")
    assert status == 404, not_found
    assert not_found["error"]["code"] == "FrontendApiPathNotFound", not_found

    status, method_not_allowed = fetch_error_json("/api/remediation-tickets/ticket/status", method="POST")
    assert status == 405, method_not_allowed
    assert method_not_allowed["error"]["code"] == "MethodNotAllowed", method_not_allowed

    summary = {
        "status": "passed",
        "base_url": base_url,
        "health": health,
        "checked_paths": [
            "/__health",
            "/__endpoints",
            "/api/dashboard/today",
            "/api/remediation-tickets?status=open",
            "/api/ai-evidence/sec-event-aapl-10k-20240928",
            "/api/source-documents/aapl-2024-10k-20240928",
            "/api/events?asOfDate=2024-11-01",
            "/api/themes/ANNUAL_REPORTING?asOfDate=2024-11-01",
            "/api/performance/Long%20Term%20Paper/outcomes?measurementEndDate=2024-12-02",
            "/api/not-found",
        ],
    }
    (artifact_root / "runtime-smoke.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)
PY

env -u STOCKANALYSIS_PSQL_COMMAND PYTHONPATH=src python3 - "$ARTIFACT_ROOT" <<'PY'
from __future__ import annotations

import json
import sys
import threading
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import urlopen

from stockanalysis.frontend.fixture_server import create_frontend_fixture_server

artifact_root = Path(sys.argv[1])


def start_server(source: str):
    server = create_frontend_fixture_server(port=0, source=source)
    host, port = server.server_address
    base_url = f"http://{host}:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, base_url


def fetch_json(base_url: str, path: str) -> tuple[int, dict[str, Any]]:
    with urlopen(f"{base_url}{path}", timeout=5) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def fetch_error_json(base_url: str, path: str) -> tuple[int, dict[str, Any]]:
    try:
        urlopen(f"{base_url}{path}", timeout=5)
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))
    raise AssertionError(f"{path} unexpectedly succeeded")


auto_server, auto_thread, auto_base_url = start_server("auto")
try:
    status, health = fetch_json(auto_base_url, "/__health")
    assert status == 200, health
    assert health["source_mode"] == "auto", health

    status, auto_tickets = fetch_json(auto_base_url, "/api/remediation-tickets?status=open")
    assert status == 200, auto_tickets
    assert auto_tickets["data"]["tickets"][0]["symbol"] == "BABA", auto_tickets
finally:
    auto_server.shutdown()
    auto_server.server_close()
    auto_thread.join(timeout=5)

live_server, live_thread, live_base_url = start_server("live")
try:
    status, live_error = fetch_error_json(live_base_url, "/api/remediation-tickets?status=open")
    assert status == 503, live_error
    assert live_error["error"]["code"] == "FrontendLiveReadUnavailable", live_error
    assert live_error["error"]["details"]["source_mode"] == "live", live_error
finally:
    live_server.shutdown()
    live_server.server_close()
    live_thread.join(timeout=5)

summary = {
    "status": "passed",
    "checked_source_modes": ["fixture", "auto", "live"],
    "auto_source_mode": "fixture_fallback_without_db_config",
    "live_missing_config_status": 503,
}
(artifact_root / "source-mode-smoke.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
PY

if [ -e app ]; then
  echo "root-level app scaffold should not exist; use apps/web instead" >&2
  exit 1
fi

echo "frontend fixture server verification passed"
