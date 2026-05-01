#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
CONTAINER_NAME="${PORTFOLIO_REMEDIATION_SCHEDULER_RUNTIME_VERIFY_CONTAINER_NAME:-stockanalysis-portfolio-remediation-scheduler-runtime-verify}"
POSTGRES_IMAGE="${PORTFOLIO_REMEDIATION_SCHEDULER_RUNTIME_VERIFY_POSTGRES_IMAGE:-postgres:16-alpine}"
POSTGRES_DB="${PORTFOLIO_REMEDIATION_SCHEDULER_RUNTIME_VERIFY_POSTGRES_DB:-stockanalysis}"
POSTGRES_USER="${PORTFOLIO_REMEDIATION_SCHEDULER_RUNTIME_VERIFY_POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${PORTFOLIO_REMEDIATION_SCHEDULER_RUNTIME_VERIFY_POSTGRES_PASSWORD:-postgres}"
ARTIFACT_DIR=$(mktemp -d /tmp/stockanalysis-portfolio-remediation-scheduler-runtime.XXXXXX)
SCHEDULER_ARTIFACT_ROOT="$ARTIFACT_DIR/scheduler-artifacts"

cleanup() {
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  rm -rf "$ARTIFACT_DIR"
}

trap cleanup EXIT

cleanup

cd "$ROOT_DIR"

python3 -m compileall src tests >/dev/null
PYTHONPATH=src python3 -m unittest discover -s tests -v
bash -n scripts/run_portfolio_remediation_daily_scheduler.sh

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

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli market-universe-bootstrap \
  --company-tickers-json tests/fixtures/sec_company_tickers_exchange_sample.json \
  --exchange Nasdaq \
  --exchange NYSE >/dev/null

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli market-price-universe-backfill \
  --fixtures-dir tests/fixtures \
  --exchange Nasdaq \
  --exchange NYSE >/dev/null

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli strategy-universe-slice \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --exchange Nasdaq \
  --exchange NYSE \
  --min-observation-count 2 \
  --min-adjusted-close 50 \
  --limit 10 >/dev/null

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli market-feature-snapshot \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --feature-set-version bootstrap-v1 >/dev/null

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli sec-filings-upsert \
  --cik 320193 \
  --submissions-json tests/fixtures/sec_submissions_CIK0000320193.json >/dev/null

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli sec-filing-raw-fetch \
  --external-document-id 0000320193-24-000123 \
  --body-file tests/fixtures/sec_filing_aapl_20240928_10k.html \
  --artifact-root "$ARTIFACT_DIR" >/dev/null

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli sec-filings-event-extract \
  --external-document-id 0000320193-24-000123 >/dev/null

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli event-classification-impact-bootstrap \
  --limit 20 >/dev/null

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli event-instrument-impact-bootstrap \
  --limit 20 >/dev/null

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli instrument-theme-enrichment \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 >/dev/null

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli cycle-state-snapshot \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --score-version bootstrap-v1 >/dev/null

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli recommendation-bootstrap \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --score-version bootstrap-v1 >/dev/null

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli thesis-bootstrap \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --thesis-version bootstrap-v1 >/dev/null

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli thesis-review-bootstrap \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --review-version bootstrap-v1 >/dev/null

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli market-price-upsert \
  --symbol AAPL \
  --prices-json tests/fixtures/alpha_vantage_daily_adjusted_AAPL_outcome.json >/dev/null

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli performance-outcome-batch-bootstrap \
  --as-of-date 2024-11-01 \
  --measurement-end-date 2024-12-02 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --outcome-version bootstrap-v1 >/dev/null

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli portfolio-position-snapshot-upsert \
  --positions-csv tests/fixtures/portfolio_positions_long_term_paper_with_gap.csv \
  --portfolio-name "Long Term Paper" \
  --snapshot-date 2024-11-01 \
  --strategy-name long_term_core >/dev/null

mkdir -p "$SCHEDULER_ARTIFACT_ROOT"
wrapper_output_path_file="$ARTIFACT_DIR/scheduler-output-path.txt"

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PORTFOLIO_REMEDIATION_AS_OF_DATE="2024-11-01" \
PORTFOLIO_REMEDIATION_UNIVERSE_VERSION="fixture-v1" \
PORTFOLIO_REMEDIATION_COVERAGE_MEASUREMENT_END_DATE="2024-12-02" \
PORTFOLIO_REMEDIATION_TICKET_LIMIT="5" \
PORTFOLIO_REMEDIATION_ARTIFACT_ROOT="$SCHEDULER_ARTIFACT_ROOT" \
scripts/run_portfolio_remediation_daily_scheduler.sh > "$wrapper_output_path_file"

scheduler_json_path=$(cat "$wrapper_output_path_file")
scheduler_stderr_count=$(find "$SCHEDULER_ARTIFACT_ROOT" -name "*portfolio-remediation-daily.stderr.log" | wc -l | tr -d ' ')
daily_run_status=$(docker exec "$CONTAINER_NAME" psql -t -A -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select status from ops.pipeline_run where pipeline_name = 'portfolio_remediation_daily_automation' order by run_id desc limit 1;")

python3 - "$scheduler_json_path" "$SCHEDULER_ARTIFACT_ROOT" "$scheduler_stderr_count" "$daily_run_status" <<'PY'
import json
import os
import sys

json_path, artifact_root, stderr_count, run_status = sys.argv[1:]

assert json_path.startswith(artifact_root + os.sep), json_path
assert os.path.isfile(json_path), json_path
assert stderr_count == "1", stderr_count

with open(json_path, "r", encoding="utf-8") as handle:
    payload = json.load(handle)

assert payload["report_name"] == "portfolio_remediation_daily_automation", payload
assert payload["portfolio_name"] == "Long Term Paper", payload
assert payload["as_of_date"] == "2024-11-01", payload
assert payload["coverage_measurement_end_date"] == "2024-12-02", payload
assert payload["run_id"], payload
assert [step["name"] for step in payload["steps"]] == [
    "portfolio_review_bootstrap",
    "portfolio_remediation_ticket_bootstrap",
    "portfolio_remediation_ticket_report",
], payload

review = payload["review"]
assert review["review_item_count"] == 2, payload
assert review["action_counts"]["monitor"] == 1, payload
assert review["action_counts"]["needs_thesis_review"] == 1, payload

ticket_report = payload["ticket_report"]
assert ticket_report["ticket_count"] == 1, payload
assert ticket_report["status_counts"] == {"open": 1}, payload
ticket = ticket_report["tickets"][0]
assert ticket["symbol"] == "BABA", payload
assert ticket["status"] == "open", payload
assert ticket["remediation_type"] == "thesis_remediation", payload
assert ticket["suggested_runner"] == "thesis_or_position_link_review", payload
assert "coverage status missing_thesis" in ticket["reason"], payload

assert run_status.strip() == "succeeded", run_status
PY
