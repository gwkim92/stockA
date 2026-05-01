#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
CONTAINER_NAME="${SEC_EVENT_EXTRACT_VERIFY_CONTAINER_NAME:-stockanalysis-sec-event-extract-verify}"
POSTGRES_IMAGE="${SEC_EVENT_EXTRACT_VERIFY_POSTGRES_IMAGE:-postgres:16-alpine}"
POSTGRES_DB="${SEC_EVENT_EXTRACT_VERIFY_POSTGRES_DB:-stockanalysis}"
POSTGRES_USER="${SEC_EVENT_EXTRACT_VERIFY_POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${SEC_EVENT_EXTRACT_VERIFY_POSTGRES_PASSWORD:-postgres}"
ARTIFACT_DIR=$(mktemp -d /tmp/stockanalysis-sec-event-extract.XXXXXX)

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

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli sec-filings-event-extract \
  --external-document-id 0000320193-24-000123 >/dev/null

event_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from event.event e join event.event_document_link l on l.event_id = e.event_id join ingest.source_document d on d.document_id = l.document_id where d.external_document_id = '0000320193-24-000123' and e.event_type = 'sec_annual_report_filed';")
dedupe_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from event.event where dedupe_key = 'sec_edgar:0000320193-24-000123:sec_annual_report_filed';")
run_status=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select status from ops.pipeline_run where pipeline_name = 'sec_filings_event_extract' order by run_id desc limit 1;")

test "$event_count" = "1"
test "$dedupe_count" = "1"
test "$run_status" = "succeeded"
