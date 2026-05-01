#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
CONTAINER_NAME="${STRATEGY_UNIVERSE_VERIFY_CONTAINER_NAME:-stockanalysis-strategy-universe-verify}"
POSTGRES_IMAGE="${STRATEGY_UNIVERSE_VERIFY_POSTGRES_IMAGE:-postgres:16-alpine}"
POSTGRES_DB="${STRATEGY_UNIVERSE_VERIFY_POSTGRES_DB:-stockanalysis}"
POSTGRES_USER="${STRATEGY_UNIVERSE_VERIFY_POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${STRATEGY_UNIVERSE_VERIFY_POSTGRES_PASSWORD:-postgres}"

cleanup() {
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
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

batch_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from signal.strategy_universe_batch where strategy_name = 'long_term_core' and universe_version = 'fixture-v1';")
member_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from signal.strategy_universe_member;")
aapl_member_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from signal.strategy_universe_member m join ref.instrument i on i.instrument_id = m.instrument_id where i.primary_symbol = 'AAPL' and m.rank_position = 1;")
baba_member_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from signal.strategy_universe_member m join ref.instrument i on i.instrument_id = m.instrument_id where i.primary_symbol = 'BABA' and m.rank_position = 2;")
linked_run_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from signal.strategy_universe_batch where source_run_id is not null;")
run_status=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select status from ops.pipeline_run where pipeline_name = 'strategy_universe_slice' order by run_id desc limit 1;")

test "$batch_count" = "1"
test "$member_count" = "2"
test "$aapl_member_count" = "1"
test "$baba_member_count" = "1"
test "$linked_run_count" = "1"
test "$run_status" = "succeeded"
