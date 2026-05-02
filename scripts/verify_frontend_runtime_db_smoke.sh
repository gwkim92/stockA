#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
CONTAINER_NAME="${FRONTEND_RUNTIME_DB_SMOKE_CONTAINER_NAME:-stockanalysis-frontend-runtime-db-smoke}"
POSTGRES_IMAGE="${FRONTEND_RUNTIME_DB_SMOKE_POSTGRES_IMAGE:-postgres:16-alpine}"
POSTGRES_DB="${FRONTEND_RUNTIME_DB_SMOKE_POSTGRES_DB:-stockanalysis}"
POSTGRES_USER="${FRONTEND_RUNTIME_DB_SMOKE_POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${FRONTEND_RUNTIME_DB_SMOKE_POSTGRES_PASSWORD:-postgres}"
ARTIFACT_DIR=$(mktemp -d /tmp/stockanalysis-frontend-runtime-db-smoke.XXXXXX)
READ_TOKEN="frontend-runtime-db-smoke-token"

cleanup() {
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  rm -rf "$ARTIFACT_DIR"
}

run_ingest() {
  STOCKANALYSIS_PSQL_COMMAND="$PSQL_COMMAND" \
  PYTHONPATH=src python3 -m stockanalysis.ingest.cli "$@" >/dev/null
}

trap cleanup EXIT

cleanup

cd "$ROOT_DIR"

bash -n scripts/verify_frontend_runtime_db_smoke.sh
python3 -m compileall src tests >/dev/null
PYTHONPATH=src python3 -m unittest tests.test_frontend_fixture_server tests.test_frontend_live_adapter -v

docker run \
  --name "$CONTAINER_NAME" \
  -e POSTGRES_DB="$POSTGRES_DB" \
  -e POSTGRES_USER="$POSTGRES_USER" \
  -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
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

STOCKANALYSIS_PSQL_COMMAND="$PSQL_COMMAND" \
STOCKANALYSIS_FRONTEND_API_READ_TOKEN="$READ_TOKEN" \
PYTHONPATH=src python3 - "$ARTIFACT_DIR" "$READ_TOKEN" <<'PY'
from __future__ import annotations

import json
import sys
import threading
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from stockanalysis.frontend.fixture_server import create_frontend_fixture_server

artifact_dir = Path(sys.argv[1])
read_token = sys.argv[2]


def fetch_json(base_url: str, path: str, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    request = Request(f"{base_url}{path}", headers=headers or {})
    with urlopen(request, timeout=10) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def fetch_error_json(base_url: str, path: str, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    request = Request(f"{base_url}{path}", headers=headers or {})
    try:
        urlopen(request, timeout=10)
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))
    raise AssertionError(f"{path} unexpectedly succeeded")


server = create_frontend_fixture_server(
    port=0,
    source="live",
    runtime_profile="production",
    allowed_origin="https://cockpit.example",
    auth_mode="read-token",
)
host, port = server.server_address
base_url = f"http://{host}:{port}"
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()

try:
    status, health = fetch_json(base_url, "/__health")
    assert status == 200, health
    assert health["source_mode"] == "live", health
    assert health["runtime"]["runtime_profile"] == "production", health
    assert health["runtime"]["read_auth_required"] is True, health
    assert health["runtime"]["allowed_origin"] == "https://cockpit.example", health

    status, unauthorized = fetch_error_json(base_url, "/api/dashboard/today")
    assert status == 401, unauthorized
    assert unauthorized["error"]["code"] == "Unauthorized", unauthorized

    headers = {"Authorization": f"Bearer {read_token}"}

    status, dashboard = fetch_json(base_url, "/api/dashboard/today", headers=headers)
    assert status == 200, dashboard
    assert dashboard["data"]["portfolio_name"] == "Long Term Paper", dashboard
    assert dashboard["data"]["run_status"]["daily_automation"] == "succeeded", dashboard
    assert dashboard["data"]["attention_summary"]["open_ticket_count"] >= 1, dashboard
    assert dashboard["data"]["attention_summary"]["missing_thesis_count"] == 1, dashboard

    status, health_payload = fetch_json(base_url, "/api/data-health", headers=headers)
    assert status == 200, health_payload
    assert health_payload["data"]["overall_status"] in {"ok", "attention_required"}, health_payload
    assert any(item["pipeline_name"] == "portfolio_remediation_daily_automation" for item in health_payload["data"]["pipeline_runs"]), health_payload

    status, cycles = fetch_json(base_url, "/api/cycles?asOfDate=2024-11-01", headers=headers)
    assert status == 200, cycles
    assert cycles["data"]["strategy_name"] == "long_term_core", cycles
    assert any(item["theme_key"] == "ANNUAL_REPORTING" for item in cycles["data"]["cycle_states"]), cycles

    status, events = fetch_json(base_url, "/api/events?asOfDate=2024-11-01", headers=headers)
    assert status == 200, events
    assert events["data"]["summary"]["event_count"] >= 1, events
    assert events["data"]["events"][0]["symbol"] == "AAPL", events

    status, theme = fetch_json(base_url, "/api/themes/ANNUAL_REPORTING?asOfDate=2024-11-01", headers=headers)
    assert status == 200, theme
    assert theme["data"]["theme_key"] == "ANNUAL_REPORTING", theme
    assert any(item["symbol"] == "AAPL" for item in theme["data"]["linked_instruments"]), theme

    status, tickets = fetch_json(base_url, "/api/remediation-tickets?status=open", headers=headers)
    assert status == 200, tickets
    assert tickets["data"]["ticket_count"] >= 1, tickets
    assert any(ticket["symbol"] == "BABA" for ticket in tickets["data"]["tickets"]), tickets

    status, recommendation = fetch_json(base_url, "/api/recommendations/AAPL-2024-11-01", headers=headers)
    assert status == 200, recommendation
    assert recommendation["data"]["symbol"] == "AAPL", recommendation
    assert recommendation["data"]["outcome"]["label"] == "outperform", recommendation

    status, thesis = fetch_json(base_url, "/api/theses/AAPL-bootstrap-v1", headers=headers)
    assert status == 200, thesis
    assert thesis["data"]["symbol"] == "AAPL", thesis
    assert thesis["data"]["latest_review"]["action"] != "unreviewed", thesis

    status, performance = fetch_json(
        base_url,
        "/api/performance/Long%20Term%20Paper/outcomes?measurementEndDate=2024-12-02",
        headers=headers,
    )
    assert status == 200, performance
    assert performance["data"]["summary"]["measured_recommendation_count"] >= 1, performance
    assert any(item["symbol"] == "AAPL" for item in performance["data"]["outcomes"]), performance

    status, source_document = fetch_json(base_url, "/api/source-documents/0000320193-24-000123", headers=headers)
    assert status == 200, source_document
    assert source_document["data"]["symbol"] == "AAPL", source_document
    assert source_document["data"]["access_policy"]["browser_download_enabled"] is False, source_document

    summary = {
        "status": "passed",
        "base_url": base_url,
        "checked_endpoints": [
            "/__health",
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
        ],
    }
    (artifact_dir / "frontend-runtime-db-smoke.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=10)
PY

echo "frontend runtime DB smoke verification passed"
