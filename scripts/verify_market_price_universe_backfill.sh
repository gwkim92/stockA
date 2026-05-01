#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
CONTAINER_NAME="${MARKET_PRICE_UNIVERSE_BACKFILL_VERIFY_CONTAINER_NAME:-stockanalysis-market-price-universe-backfill-verify}"
POSTGRES_IMAGE="${MARKET_PRICE_UNIVERSE_BACKFILL_POSTGRES_IMAGE:-postgres:16-alpine}"
POSTGRES_DB="${MARKET_PRICE_UNIVERSE_BACKFILL_POSTGRES_DB:-stockanalysis}"
POSTGRES_USER="${MARKET_PRICE_UNIVERSE_BACKFILL_POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${MARKET_PRICE_UNIVERSE_BACKFILL_POSTGRES_PASSWORD:-postgres}"

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

bar_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from market.daily_price_bar;")
aapl_bar_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from market.daily_price_bar b join ref.instrument i on i.instrument_id = b.instrument_id where i.primary_symbol = 'AAPL';")
baba_bar_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from market.daily_price_bar b join ref.instrument i on i.instrument_id = b.instrument_id where i.primary_symbol = 'BABA';")
source_run_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from market.daily_price_bar where source_run_id is not null;")
succeeded_run_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from ops.pipeline_run where pipeline_name = 'market_price_upsert' and status = 'succeeded';")

test "$bar_count" = "4"
test "$aapl_bar_count" = "2"
test "$baba_bar_count" = "2"
test "$source_run_count" = "4"
test "$succeeded_run_count" = "2"
