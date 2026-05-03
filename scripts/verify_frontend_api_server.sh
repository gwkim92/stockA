#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
WEB_DIR="$ROOT_DIR/apps/web"
PYTHON_BIN="${PYTHON_BIN:-python3}"
CONTAINER_NAME="${FRONTEND_API_SERVER_VERIFY_CONTAINER_NAME:-stockanalysis-frontend-api-server-verify}"
POSTGRES_IMAGE="${FRONTEND_API_SERVER_VERIFY_POSTGRES_IMAGE:-postgres:16-alpine}"
POSTGRES_DB="${FRONTEND_API_SERVER_VERIFY_POSTGRES_DB:-stockanalysis}"
POSTGRES_USER="${FRONTEND_API_SERVER_VERIFY_POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${FRONTEND_API_SERVER_VERIFY_POSTGRES_PASSWORD:-postgres}"
ARTIFACT_DIR=$(mktemp -d /tmp/stockanalysis-frontend-api-server.XXXXXX)
READ_TOKEN="frontend-api-server-smoke-token"
API_PID=""
WEB_PID=""

cleanup() {
  if [ -n "$WEB_PID" ]; then
    kill "$WEB_PID" >/dev/null 2>&1 || true
    wait "$WEB_PID" >/dev/null 2>&1 || true
  fi
  if [ -n "$API_PID" ]; then
    kill "$API_PID" >/dev/null 2>&1 || true
    wait "$API_PID" >/dev/null 2>&1 || true
  fi
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  rm -rf "$WEB_DIR/.next" "$WEB_DIR/tsconfig.tsbuildinfo"
  rm -rf "$ARTIFACT_DIR"
}

free_port() {
  "$PYTHON_BIN" - <<'PY'
import socket

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
}

wait_for_url() {
  local url="$1"
  "$PYTHON_BIN" - "$url" <<'PY'
import sys
import time
from urllib.request import urlopen

url = sys.argv[1]
last_error = None
for _ in range(120):
    try:
        with urlopen(url, timeout=2) as response:
            if 200 <= response.status < 500:
                raise SystemExit(0)
    except Exception as exc:
        last_error = exc
    time.sleep(0.25)
raise SystemExit(f"Timed out waiting for {url}: {last_error}")
PY
}

run_ingest() {
  STOCKANALYSIS_PSQL_COMMAND="$PSQL_COMMAND" \
  PYTHONPATH=src "$PYTHON_BIN" -m stockanalysis.ingest.cli "$@" >/dev/null
}

trap cleanup EXIT

cleanup

cd "$ROOT_DIR"

bash -n scripts/verify_frontend_api_server.sh
"$PYTHON_BIN" -m compileall src tests >/dev/null
PYTHONPATH=src "$PYTHON_BIN" -m unittest tests.test_frontend_api_server tests.test_frontend_db_pool -v
test -f src/stockanalysis/frontend/api_server.py
test -f src/stockanalysis/frontend/db_pool.py

docker run \
  --name "$CONTAINER_NAME" \
  -e POSTGRES_DB="$POSTGRES_DB" \
  -e POSTGRES_USER="$POSTGRES_USER" \
  -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  -p 127.0.0.1::5432 \
  -d "$POSTGRES_IMAGE" >/dev/null

for _ in $(seq 1 60); do
  if docker exec "$CONTAINER_NAME" pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

docker exec "$CONTAINER_NAME" pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null

for migration in "$ROOT_DIR"/db/migrations/*.sql; do
  docker exec -i "$CONTAINER_NAME" psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$migration" >/dev/null
done

for seed in "$ROOT_DIR"/db/seeds/*.sql; do
  [ -e "$seed" ] || continue
  docker exec -i "$CONTAINER_NAME" psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$seed" >/dev/null
done

HOST_PORT=$(docker port "$CONTAINER_NAME" 5432/tcp | sed 's/.*://')
DATABASE_URL="postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@127.0.0.1:$HOST_PORT/$POSTGRES_DB"
PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB"

run_ingest market-universe-bootstrap \
  --company-tickers-json tests/fixtures/sec_company_tickers_exchange_with_benchmark_sample.json \
  --exchange Nasdaq \
  --exchange NYSE

run_ingest market-price-universe-backfill \
  --fixtures-dir tests/fixtures \
  --exchange Nasdaq \
  --exchange NYSE

run_ingest strategy-universe-slice \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --exchange Nasdaq \
  --exchange NYSE \
  --min-observation-count 2 \
  --min-adjusted-close 50 \
  --limit 10

run_ingest market-feature-snapshot \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --feature-set-version bootstrap-v1

run_ingest sec-filings-upsert \
  --cik 320193 \
  --submissions-json tests/fixtures/sec_submissions_CIK0000320193.json

run_ingest sec-filing-raw-fetch \
  --external-document-id 0000320193-24-000123 \
  --body-file tests/fixtures/sec_filing_aapl_20240928_10k.html \
  --artifact-root "$ARTIFACT_DIR"

run_ingest sec-filings-event-extract \
  --external-document-id 0000320193-24-000123

run_ingest event-classification-impact-bootstrap \
  --limit 20

run_ingest event-instrument-impact-bootstrap \
  --limit 20

run_ingest instrument-theme-enrichment \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1

run_ingest cycle-state-snapshot \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --score-version bootstrap-v1

run_ingest recommendation-bootstrap \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --score-version bootstrap-v1

run_ingest thesis-bootstrap \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --thesis-version bootstrap-v1

run_ingest thesis-review-bootstrap \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --review-version bootstrap-v1

run_ingest market-price-upsert \
  --symbol AAPL \
  --prices-json tests/fixtures/alpha_vantage_daily_adjusted_AAPL_outcome.json

run_ingest performance-outcome-batch-bootstrap \
  --as-of-date 2024-11-01 \
  --measurement-end-date 2024-12-02 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --outcome-version bootstrap-v1

run_ingest portfolio-position-snapshot-upsert \
  --positions-csv tests/fixtures/portfolio_positions_long_term_paper_with_gap.csv \
  --portfolio-name "Long Term Paper" \
  --snapshot-date 2024-11-01 \
  --strategy-name long_term_core

run_ingest portfolio-attribution-bootstrap \
  --portfolio-name "Long Term Paper" \
  --snapshot-date 2024-11-01 \
  --measurement-end-date 2024-12-02 \
  --methodology position_weighted_alpha_v1

run_ingest portfolio-remediation-daily-run \
  --portfolio-name "Long Term Paper" \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --review-version bootstrap-v1 \
  --coverage-measurement-end-date 2024-12-02 \
  --ticket-limit 5 \
  --ticket-status open

API_PORT=$(free_port)
API_BASE_URL="http://127.0.0.1:$API_PORT"
STOCKANALYSIS_DATABASE_URL="$DATABASE_URL" \
STOCKANALYSIS_FRONTEND_RUNTIME_PROFILE="production" \
STOCKANALYSIS_FRONTEND_API_ALLOWED_ORIGIN="https://cockpit.example" \
STOCKANALYSIS_FRONTEND_API_AUTH_MODE="read-token" \
STOCKANALYSIS_FRONTEND_API_READ_TOKEN="$READ_TOKEN" \
PYTHONPATH=src "$PYTHON_BIN" -m uvicorn stockanalysis.frontend.api_server:create_app \
  --factory \
  --host 127.0.0.1 \
  --port "$API_PORT" \
  --log-level warning \
  > "$ARTIFACT_DIR/api-server.log" \
  2> "$ARTIFACT_DIR/api-server.err" &
API_PID=$!

wait_for_url "$API_BASE_URL/__health"

"$PYTHON_BIN" - "$API_BASE_URL" "$READ_TOKEN" <<'PY'
from __future__ import annotations

import json
import sys
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

base_url = sys.argv[1]
read_token = sys.argv[2]


def fetch_json(path: str, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    request = Request(f"{base_url}{path}", headers=headers or {})
    with urlopen(request, timeout=10) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def fetch_error_json(path: str, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    request = Request(f"{base_url}{path}", headers=headers or {})
    try:
        urlopen(request, timeout=10)
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))
    raise AssertionError(f"{path} unexpectedly succeeded")


status, health = fetch_json("/__health")
assert status == 200, health
assert health["service"] == "frontend-api-server", health
assert health["runtime"]["runtime_profile"] == "production", health
assert health["connection_boundary"] == "psycopg_pool", health
assert "database_url" not in health["runtime"], health

status, unauthorized = fetch_error_json("/api/dashboard/today")
assert status == 401, unauthorized
assert unauthorized["error"]["code"] == "Unauthorized", unauthorized

headers = {"Authorization": f"Bearer {read_token}"}

for path in [
    "/__endpoints",
    "/api/dashboard/today",
    "/api/data-health",
    "/api/cycles?asOfDate=2024-11-01",
    "/api/events?asOfDate=2024-11-01",
    "/api/themes/ANNUAL_REPORTING?asOfDate=2024-11-01",
    "/api/remediation-tickets?status=open",
    "/api/recommendations/AAPL-2024-11-01",
    "/api/theses/AAPL-bootstrap-v1",
    "/api/performance/Long%20Term%20Paper/outcomes?measurementEndDate=2024-12-02",
    "/api/source-documents/0000320193-24-000123",
]:
    status, payload = fetch_json(path, headers=headers)
    assert status == 200, (path, payload)
    assert payload["contract_version"] == "frontend-api-v0.1", (path, payload)

status, dashboard = fetch_json("/api/dashboard/today", headers=headers)
assert dashboard["data"]["portfolio_name"] == "Long Term Paper", dashboard
assert dashboard["data"]["attention_summary"]["missing_thesis_count"] == 1, dashboard

status, tickets = fetch_json("/api/remediation-tickets?status=open", headers=headers)
assert any(ticket["symbol"] == "BABA" for ticket in tickets["data"]["tickets"]), tickets
PY

cd "$WEB_DIR"
npm install --no-audit --fund=false
npm run typecheck
STOCKANALYSIS_FRONTEND_API_BASE_URL="$API_BASE_URL" \
STOCKANALYSIS_FRONTEND_API_READ_TOKEN="$READ_TOKEN" \
npm run build

WEB_PORT=$(free_port)
WEB_BASE_URL="http://127.0.0.1:$WEB_PORT"
STOCKANALYSIS_FRONTEND_API_BASE_URL="$API_BASE_URL" \
STOCKANALYSIS_FRONTEND_API_READ_TOKEN="$READ_TOKEN" \
npm run start -- -p "$WEB_PORT" \
  > "$ARTIFACT_DIR/web-server.log" \
  2> "$ARTIFACT_DIR/web-server.err" &
WEB_PID=$!

wait_for_url "$WEB_BASE_URL"

"$PYTHON_BIN" - "$WEB_BASE_URL" <<'PY'
import sys
from urllib.request import urlopen

base_url = sys.argv[1]
with urlopen(base_url, timeout=10) as response:
    body = response.read().decode("utf-8")
assert response.status == 200, response.status
assert "Long-term portfolio review starts" in body, body[:500]
assert "BABA" in body, body[:500]
PY

cd "$ROOT_DIR"
echo "frontend API server verification passed"
