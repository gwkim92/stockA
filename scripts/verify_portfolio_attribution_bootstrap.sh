#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
CONTAINER_NAME="${PORTFOLIO_ATTRIBUTION_BOOTSTRAP_VERIFY_CONTAINER_NAME:-stockanalysis-portfolio-attribution-bootstrap-verify}"
POSTGRES_IMAGE="${PORTFOLIO_ATTRIBUTION_BOOTSTRAP_VERIFY_POSTGRES_IMAGE:-postgres:16-alpine}"
POSTGRES_DB="${PORTFOLIO_ATTRIBUTION_BOOTSTRAP_VERIFY_POSTGRES_DB:-stockanalysis}"
POSTGRES_USER="${PORTFOLIO_ATTRIBUTION_BOOTSTRAP_VERIFY_POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${PORTFOLIO_ATTRIBUTION_BOOTSTRAP_VERIFY_POSTGRES_PASSWORD:-postgres}"
ARTIFACT_DIR=$(mktemp -d /tmp/stockanalysis-portfolio-attribution-bootstrap.XXXXXX)

cleanup() {
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  rm -rf "$ARTIFACT_DIR"
}

trap cleanup EXIT

cleanup

cd "$ROOT_DIR"

python3 -m compileall src tests >/dev/null
PYTHONPATH=src python3 -m unittest discover -s tests -v

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
  --company-tickers-json tests/fixtures/sec_company_tickers_exchange_with_benchmark_sample.json \
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
PYTHONPATH=src python3 -m stockanalysis.ingest.cli market-price-upsert \
  --symbol AAPL \
  --prices-json tests/fixtures/alpha_vantage_daily_adjusted_AAPL_outcome.json >/dev/null

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli performance-outcome-batch-bootstrap \
  --as-of-date 2024-11-01 \
  --measurement-end-date 2024-11-04 \
  --measurement-end-date 2024-12-02 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --outcome-version bootstrap-v1 >/dev/null

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli portfolio-position-snapshot-upsert \
  --positions-csv tests/fixtures/portfolio_positions_long_term_paper.csv \
  --portfolio-name "Long Term Paper" \
  --snapshot-date 2024-11-01 \
  --strategy-name long_term_core >/dev/null

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli portfolio-attribution-bootstrap \
  --portfolio-name "Long Term Paper" \
  --snapshot-date 2024-11-01 \
  --measurement-end-date 2024-12-02 \
  --methodology position_weighted_alpha_v1 >/dev/null

attribution_run_table_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from information_schema.tables where table_schema = 'performance' and table_name = 'attribution_run';")
attribution_component_table_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from information_schema.tables where table_schema = 'performance' and table_name = 'attribution_component';")
attribution_run_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from performance.attribution_run attribution join portfolio.portfolio portfolio on portfolio.portfolio_id = attribution.portfolio_id where portfolio.portfolio_name = 'Long Term Paper' and attribution.snapshot_date = '2024-11-01' and attribution.measurement_start_date = '2024-11-01' and attribution.measurement_end_date = '2024-12-02' and attribution.methodology = 'position_weighted_alpha_v1';")
attribution_component_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from performance.attribution_component component join performance.attribution_run attribution on attribution.attribution_run_id = component.attribution_run_id join portfolio.portfolio portfolio on portfolio.portfolio_id = attribution.portfolio_id where portfolio.portfolio_name = 'Long Term Paper' and attribution.snapshot_date = '2024-11-01' and attribution.measurement_end_date = '2024-12-02';")
aapl_security_component_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from performance.attribution_component component join performance.attribution_run attribution on attribution.attribution_run_id = component.attribution_run_id join ref.instrument instrument on instrument.instrument_id = component.instrument_id where attribution.snapshot_date = '2024-11-01' and attribution.measurement_end_date = '2024-12-02' and component.component_type = 'security_selection' and component.component_key = 'AAPL' and instrument.primary_symbol = 'AAPL' and component.weight = 0.0500 and component.return_pct = 0.100000 and component.benchmark_return_pct = 0.040000 and component.alpha_pct = 0.060000 and component.contribution_bps = 30.0000;")
annual_reporting_component_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from performance.attribution_component component join performance.attribution_run attribution on attribution.attribution_run_id = component.attribution_run_id where attribution.snapshot_date = '2024-11-01' and attribution.measurement_end_date = '2024-12-02' and component.component_type = 'theme_exposure' and component.component_key = 'ANNUAL_REPORTING' and component.weight = 0.0500 and component.alpha_pct = 0.060000 and component.contribution_bps = 30.0000;")
cash_component_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from performance.attribution_component component join performance.attribution_run attribution on attribution.attribution_run_id = component.attribution_run_id where attribution.snapshot_date = '2024-11-01' and attribution.measurement_end_date = '2024-12-02' and component.component_type = 'cash_timing' and component.component_key = 'CASH' and component.weight = 0.9500 and component.contribution_bps = 0.0000;")
source_run_linked_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from performance.attribution_run attribution join ops.pipeline_run run on run.run_id = attribution.source_run_id where run.pipeline_name = 'portfolio_attribution_bootstrap' and run.status = 'succeeded';")
run_status=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select status from ops.pipeline_run where pipeline_name = 'portfolio_attribution_bootstrap' order by run_id desc limit 1;")

test "$attribution_run_table_count" = "1"
test "$attribution_component_table_count" = "1"
test "$attribution_run_count" = "1"
test "$attribution_component_count" = "3"
test "$aapl_security_component_count" = "1"
test "$annual_reporting_component_count" = "1"
test "$cash_component_count" = "1"
test "$source_run_linked_count" = "1"
test "$run_status" = "succeeded"
