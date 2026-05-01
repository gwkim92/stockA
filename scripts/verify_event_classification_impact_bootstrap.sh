#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
CONTAINER_NAME="${EVENT_CLASSIFICATION_IMPACT_VERIFY_CONTAINER_NAME:-stockanalysis-event-classification-impact-verify}"
POSTGRES_IMAGE="${EVENT_CLASSIFICATION_IMPACT_VERIFY_POSTGRES_IMAGE:-postgres:16-alpine}"
POSTGRES_DB="${EVENT_CLASSIFICATION_IMPACT_VERIFY_POSTGRES_DB:-stockanalysis}"
POSTGRES_USER="${EVENT_CLASSIFICATION_IMPACT_VERIFY_POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${EVENT_CLASSIFICATION_IMPACT_VERIFY_POSTGRES_PASSWORD:-postgres}"
ARTIFACT_DIR=$(mktemp -d /tmp/stockanalysis-event-classification-impact.XXXXXX)

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
PYTHONPATH=src python3 -m stockanalysis.ingest.cli sec-filing-raw-fetch \
  --external-document-id 0000320193-24-000101 \
  --body-file tests/fixtures/sec_filing_aapl_20240629_10q.html \
  --artifact-root "$ARTIFACT_DIR" >/dev/null

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli sec-filings-event-batch-extract \
  --limit 10 >/dev/null

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli event-classification-impact-bootstrap \
  --limit 10 >/dev/null

node_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from ref.classification_node where taxonomy_family = 'internal_theme' and code in ('PUBLIC_COMPANY_REPORTING','ANNUAL_REPORTING','QUARTERLY_REPORTING','CURRENT_REPORTING','CORPORATE_GOVERNANCE');")
edge_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from ref.classification_edge e join ref.classification_node p on p.node_id = e.parent_node_id join ref.classification_node c on c.node_id = e.child_node_id where p.code = 'PUBLIC_COMPANY_REPORTING' and c.code in ('ANNUAL_REPORTING','QUARTERLY_REPORTING','CURRENT_REPORTING','CORPORATE_GOVERNANCE');")
impact_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from event.event_classification_impact;")
annual_impact_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from event.event_classification_impact i join event.event e on e.event_id = i.event_id join ref.classification_node n on n.node_id = i.node_id where e.event_type = 'sec_annual_report_filed' and n.code = 'ANNUAL_REPORTING';")
quarterly_impact_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from event.event_classification_impact i join event.event e on e.event_id = i.event_id join ref.classification_node n on n.node_id = i.node_id where e.event_type = 'sec_quarterly_report_filed' and n.code = 'QUARTERLY_REPORTING';")
run_status=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select status from ops.pipeline_run where pipeline_name = 'event_classification_impact_bootstrap' order by run_id desc limit 1;")

test "$node_count" = "5"
test "$edge_count" = "4"
test "$impact_count" = "2"
test "$annual_impact_count" = "1"
test "$quarterly_impact_count" = "1"
test "$run_status" = "succeeded"
