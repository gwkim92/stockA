#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
CONTAINER_NAME="${PERFORMANCE_OUTCOME_BOOTSTRAP_VERIFY_CONTAINER_NAME:-stockanalysis-performance-outcome-bootstrap-verify}"
POSTGRES_IMAGE="${PERFORMANCE_OUTCOME_BOOTSTRAP_VERIFY_POSTGRES_IMAGE:-postgres:16-alpine}"
POSTGRES_DB="${PERFORMANCE_OUTCOME_BOOTSTRAP_VERIFY_POSTGRES_DB:-stockanalysis}"
POSTGRES_USER="${PERFORMANCE_OUTCOME_BOOTSTRAP_VERIFY_POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${PERFORMANCE_OUTCOME_BOOTSTRAP_VERIFY_POSTGRES_PASSWORD:-postgres}"
ARTIFACT_DIR=$(mktemp -d /tmp/stockanalysis-performance-outcome-bootstrap.XXXXXX)

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
  --measurement-end-date 2024-11-04 \
  --measurement-end-date 2024-12-02 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --outcome-version bootstrap-v1 >/dev/null

recommendation_outcome_table_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from information_schema.tables where table_schema = 'performance' and table_name = 'recommendation_outcome';")
thesis_outcome_table_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from information_schema.tables where table_schema = 'performance' and table_name = 'thesis_outcome';")
recommendation_outcome_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from performance.recommendation_outcome;")
thesis_outcome_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from performance.thesis_outcome;")
aapl_short_recommendation_outcome_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from performance.recommendation_outcome outcome join signal.recommendation recommendation on recommendation.recommendation_id = outcome.recommendation_id join ref.instrument instrument on instrument.instrument_id = recommendation.instrument_id where instrument.primary_symbol = 'AAPL' and outcome.measurement_start_date = '2024-11-01' and outcome.measurement_end_date = '2024-11-04' and outcome.horizon_days = 3 and outcome.entry_price = 222.910000 and outcome.exit_price = 225.139100 and outcome.absolute_return_pct = 0.010000 and outcome.benchmark_code = 'SPY' and outcome.benchmark_return_pct = 0.005000 and outcome.alpha_pct = 0.005000 and outcome.max_drawdown_pct = 0.000000 and outcome.outcome_label = 'outperform';")
aapl_short_thesis_outcome_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from performance.thesis_outcome outcome join signal.investment_thesis thesis on thesis.thesis_id = outcome.thesis_id join ref.instrument instrument on instrument.instrument_id = thesis.instrument_id where instrument.primary_symbol = 'AAPL' and outcome.measurement_start_date = '2024-11-01' and outcome.measurement_end_date = '2024-11-04' and outcome.holding_days = 3 and outcome.status = 'working' and outcome.absolute_return_pct = 0.010000 and outcome.benchmark_code = 'SPY' and outcome.benchmark_return_pct = 0.005000 and outcome.alpha_pct = 0.005000 and outcome.success_grade = 'pass';")
aapl_long_recommendation_outcome_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from performance.recommendation_outcome outcome join signal.recommendation recommendation on recommendation.recommendation_id = outcome.recommendation_id join ref.instrument instrument on instrument.instrument_id = recommendation.instrument_id where instrument.primary_symbol = 'AAPL' and outcome.measurement_start_date = '2024-11-01' and outcome.measurement_end_date = '2024-12-02' and outcome.horizon_days = 31 and outcome.entry_price = 222.910000 and outcome.exit_price = 245.201000 and outcome.absolute_return_pct = 0.100000 and outcome.benchmark_code = 'SPY' and outcome.benchmark_return_pct = 0.040000 and outcome.alpha_pct = 0.060000 and outcome.max_drawdown_pct = 0.000000 and outcome.outcome_label = 'outperform';")
aapl_long_thesis_outcome_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from performance.thesis_outcome outcome join signal.investment_thesis thesis on thesis.thesis_id = outcome.thesis_id join ref.instrument instrument on instrument.instrument_id = thesis.instrument_id where instrument.primary_symbol = 'AAPL' and outcome.measurement_start_date = '2024-11-01' and outcome.measurement_end_date = '2024-12-02' and outcome.holding_days = 31 and outcome.status = 'working' and outcome.absolute_return_pct = 0.100000 and outcome.benchmark_code = 'SPY' and outcome.benchmark_return_pct = 0.040000 and outcome.alpha_pct = 0.060000 and outcome.success_grade = 'pass';")
recommendation_source_run_linked_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from performance.recommendation_outcome outcome join ops.pipeline_run run on run.run_id = outcome.source_run_id where run.pipeline_name = 'performance_outcome_bootstrap' and run.status = 'succeeded';")
thesis_source_run_linked_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from performance.thesis_outcome outcome join ops.pipeline_run run on run.run_id = outcome.source_run_id where run.pipeline_name = 'performance_outcome_bootstrap' and run.status = 'succeeded';")
run_status=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select status from ops.pipeline_run where pipeline_name = 'performance_outcome_bootstrap' order by run_id desc limit 1;")

test "$recommendation_outcome_table_count" = "1"
test "$thesis_outcome_table_count" = "1"
test "$recommendation_outcome_count" = "2"
test "$thesis_outcome_count" = "2"
test "$aapl_short_recommendation_outcome_count" = "1"
test "$aapl_short_thesis_outcome_count" = "1"
test "$aapl_long_recommendation_outcome_count" = "1"
test "$aapl_long_thesis_outcome_count" = "1"
test "$recommendation_source_run_linked_count" = "2"
test "$thesis_source_run_linked_count" = "2"
test "$run_status" = "succeeded"
