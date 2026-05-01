#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
CONTAINER_NAME="${EVENT_INTELLIGENCE_LLM_VERIFY_CONTAINER_NAME:-stockanalysis-event-intelligence-llm-verify}"
POSTGRES_IMAGE="${EVENT_INTELLIGENCE_LLM_VERIFY_POSTGRES_IMAGE:-postgres:16-alpine}"
POSTGRES_DB="${EVENT_INTELLIGENCE_LLM_VERIFY_POSTGRES_DB:-stockanalysis}"
POSTGRES_USER="${EVENT_INTELLIGENCE_LLM_VERIFY_POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${EVENT_INTELLIGENCE_LLM_VERIFY_POSTGRES_PASSWORD:-postgres}"
ARTIFACT_DIR=$(mktemp -d /tmp/stockanalysis-event-intelligence-llm.XXXXXX)

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
PYTHONPATH=src python3 -m stockanalysis.ingest.cli event-intelligence-llm-extract \
  --external-document-id 0000320193-24-000123 \
  --llm-output-json tests/fixtures/llm_sec_event_aapl_10k_structured.json \
  --max-input-chars 700 \
  --min-confidence 0.9 >/dev/null

event_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from event.event e join event.event_document_link l on l.event_id = e.event_id join ingest.source_document d on d.document_id = l.document_id where d.external_document_id = '0000320193-24-000123' and e.event_type = 'sec_annual_report_filed';")
invocation_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from ai.model_invocation where task_name = 'event-intelligence-llm-extract' and provider = 'fixture';")
chunk_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from ai.document_chunk c join ingest.source_document d on d.document_id = c.document_id where d.external_document_id = '0000320193-24-000123';")
artifact_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from ai.extraction_artifact where artifact_type = 'structured_event_candidate';")
run_status=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select status from ops.pipeline_run where pipeline_name = 'event_intelligence_llm_extract' order by run_id desc limit 1;")
prompt_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from ai.prompt_template where template_name = 'event-intelligence-llm-extract' and template_version = '2026-04-23';")

test "$event_count" = "1"
test "$invocation_count" = "1"
test "$chunk_count" = "1"
test "$artifact_count" = "1"
test "$run_status" = "succeeded"
test "$prompt_count" = "1"
