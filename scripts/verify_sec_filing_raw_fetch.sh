#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
CONTAINER_NAME="${SEC_RAW_FETCH_VERIFY_CONTAINER_NAME:-stockanalysis-sec-raw-fetch-verify}"
POSTGRES_IMAGE="${SEC_RAW_FETCH_VERIFY_POSTGRES_IMAGE:-postgres:16-alpine}"
POSTGRES_DB="${SEC_RAW_FETCH_VERIFY_POSTGRES_DB:-stockanalysis}"
POSTGRES_USER="${SEC_RAW_FETCH_VERIFY_POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${SEC_RAW_FETCH_VERIFY_POSTGRES_PASSWORD:-postgres}"
ARTIFACT_DIR=$(mktemp -d /tmp/stockanalysis-sec-raw-fetch.XXXXXX)

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
PYTHONPATH=src python3 -m stockanalysis.ingest.cli sec-filings-upsert \
  --cik 320193 \
  --submissions-json tests/fixtures/sec_submissions_CIK0000320193.json >/dev/null

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli sec-filing-raw-fetch \
  --external-document-id 0000320193-24-000123 \
  --body-file tests/fixtures/sec_filing_aapl_20240928_10k.html \
  --artifact-root "$ARTIFACT_DIR" >/dev/null

raw_uri_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from ingest.source_document d join ingest.data_source s on s.data_source_id = d.data_source_id where s.source_name = 'sec_edgar' and d.external_document_id = '0000320193-24-000123' and d.raw_storage_uri like 'file://%' and d.checksum is not null;")
run_status=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select status from ops.pipeline_run where pipeline_name = 'sec_filing_raw_fetch' order by run_id desc limit 1;")
artifact_file_count=$(find "$ARTIFACT_DIR" -type f | wc -l | tr -d ' ')

test "$raw_uri_count" = "1"
test "$run_status" = "succeeded"
test "$artifact_file_count" = "1"
