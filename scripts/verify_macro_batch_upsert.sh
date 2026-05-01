#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
CONTAINER_NAME="${MACRO_BATCH_VERIFY_CONTAINER_NAME:-stockanalysis-macro-batch-verify}"
POSTGRES_IMAGE="${MACRO_BATCH_VERIFY_POSTGRES_IMAGE:-postgres:16-alpine}"
POSTGRES_DB="${MACRO_BATCH_VERIFY_POSTGRES_DB:-stockanalysis}"
POSTGRES_USER="${MACRO_BATCH_VERIFY_POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${MACRO_BATCH_VERIFY_POSTGRES_PASSWORD:-postgres}"

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
PYTHONPATH=src python3 -m stockanalysis.ingest.cli macro-batch-upsert \
  --fixtures-dir tests/fixtures \
  --series-id CPIAUCSL \
  --series-id FEDFUNDS >/dev/null

series_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from macro.series where series_code in ('CPIAUCSL', 'FEDFUNDS');")
observation_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from macro.observation o join macro.series s on s.series_id = o.series_id where s.series_code in ('CPIAUCSL', 'FEDFUNDS');")
linked_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from macro.observation o join macro.series s on s.series_id = o.series_id where s.series_code in ('CPIAUCSL', 'FEDFUNDS') and o.source_run_id is not null;")
run_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from ops.pipeline_run where pipeline_name = 'macro_upsert' and status = 'succeeded';")

test "$series_count" = "2"
test "$observation_count" = "5"
test "$linked_count" = "5"
test "$run_count" = "2"
