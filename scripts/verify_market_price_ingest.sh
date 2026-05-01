#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
CONTAINER_NAME="${MARKET_PRICE_VERIFY_CONTAINER_NAME:-stockanalysis-market-price-verify}"
POSTGRES_IMAGE="${MARKET_PRICE_VERIFY_POSTGRES_IMAGE:-postgres:16-alpine}"
POSTGRES_DB="${MARKET_PRICE_VERIFY_POSTGRES_DB:-stockanalysis}"
POSTGRES_USER="${MARKET_PRICE_VERIFY_POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${MARKET_PRICE_VERIFY_POSTGRES_PASSWORD:-postgres}"

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

docker exec -i "$CONTAINER_NAME" psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null <<'SQL'
with inserted_issuer as (
    insert into ref.issuer (
        legal_name,
        display_name,
        country_code,
        issuer_type
    )
    values (
        'Apple Inc.',
        'Apple Inc.',
        'US',
        'operating_company'
    )
    returning issuer_id
)
insert into ref.instrument (
    issuer_id,
    exchange_id,
    market_code,
    primary_symbol,
    instrument_type,
    currency_code,
    name,
    listed_at
)
select
    i.issuer_id,
    e.exchange_id,
    'US',
    'AAPL',
    'common_stock',
    'USD',
    'Apple Inc. Common Stock',
    '1980-12-12T00:00:00Z'::timestamptz
from inserted_issuer i
join ref.exchange e
  on e.mic_code = 'XNAS';
SQL

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli market-price-upsert \
  --symbol AAPL \
  --prices-json tests/fixtures/alpha_vantage_daily_adjusted_AAPL.json >/dev/null

bar_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from market.daily_price_bar;")
latest_adjusted_close_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from market.daily_price_bar b join ref.instrument i on i.instrument_id = b.instrument_id where i.primary_symbol = 'AAPL' and b.trade_date = '2024-11-01'::date and b.adjusted_close = 222.9100;")
latest_volume_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from market.daily_price_bar b join ref.instrument i on i.instrument_id = b.instrument_id where i.primary_symbol = 'AAPL' and b.trade_date = '2024-11-01'::date and b.volume = 65276700;")
source_run_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from market.daily_price_bar where source_run_id is not null;")
run_status=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select status from ops.pipeline_run where pipeline_name = 'market_price_upsert' order by run_id desc limit 1;")

test "$bar_count" = "2"
test "$latest_adjusted_close_count" = "1"
test "$latest_volume_count" = "1"
test "$source_run_count" = "2"
test "$run_status" = "succeeded"
