#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
CONTAINER_NAME="${SEC_COMPANYFACTS_VERIFY_CONTAINER_NAME:-stockanalysis-sec-companyfacts-verify}"
POSTGRES_IMAGE="${SEC_COMPANYFACTS_VERIFY_POSTGRES_IMAGE:-postgres:16-alpine}"
POSTGRES_DB="${SEC_COMPANYFACTS_VERIFY_POSTGRES_DB:-stockanalysis}"
POSTGRES_USER="${SEC_COMPANYFACTS_VERIFY_POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${SEC_COMPANYFACTS_VERIFY_POSTGRES_PASSWORD:-postgres}"

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
PYTHONPATH=src python3 -m stockanalysis.ingest.cli sec-filings-upsert \
  --cik 320193 \
  --submissions-json tests/fixtures/sec_submissions_CIK0000320193.json >/dev/null

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
PYTHONPATH=src python3 -m stockanalysis.ingest.cli sec-companyfacts-upsert \
  --cik 320193 \
  --companyfacts-json tests/fixtures/sec_companyfacts_CIK0000320193.json >/dev/null

period_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from market.financial_statement_period;")
metric_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from market.financial_metric_value;")
linked_period_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from market.financial_statement_period where source_document_id is not null;")
annual_revenue_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from market.financial_metric_value v join market.financial_statement_period p on p.period_id = v.period_id where p.statement_scope = 'annual' and v.metric_code = 'revenue' and v.metric_value = 391035000000;")
quarterly_net_income_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from market.financial_metric_value v join market.financial_statement_period p on p.period_id = v.period_id where p.statement_scope = 'quarterly' and v.metric_code = 'net_income' and v.metric_value = 21448000000;")
run_status=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select status from ops.pipeline_run where pipeline_name = 'sec_companyfacts_upsert' order by run_id desc limit 1;")

test "$period_count" = "2"
test "$metric_count" = "4"
test "$linked_period_count" = "2"
test "$annual_revenue_count" = "1"
test "$quarterly_net_income_count" = "1"
test "$run_status" = "succeeded"
