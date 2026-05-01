#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
CONTAINER_NAME="${DDL_VERIFY_CONTAINER_NAME:-stockanalysis-ddl-verify}"
POSTGRES_IMAGE="${DDL_VERIFY_POSTGRES_IMAGE:-postgres:16-alpine}"
POSTGRES_DB="${DDL_VERIFY_POSTGRES_DB:-stockanalysis}"
POSTGRES_USER="${DDL_VERIFY_POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${DDL_VERIFY_POSTGRES_PASSWORD:-postgres}"
INCLUDE_SEEDS="${DDL_VERIFY_INCLUDE_SEEDS:-0}"

cleanup() {
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
}

trap cleanup EXIT

cleanup

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
  echo "Applying $(basename "$migration")"
  docker exec -i "$CONTAINER_NAME" psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$migration" >/dev/null
done

if [ "$INCLUDE_SEEDS" = "1" ]; then
  for seed in "$ROOT_DIR"/db/seeds/*.sql; do
    [ -e "$seed" ] || continue
    echo "Applying seed $(basename "$seed")"
    docker exec -i "$CONTAINER_NAME" psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$seed" >/dev/null
  done
fi

echo "Created tables:"
docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "
select schemaname || '.' || tablename
from pg_tables
where schemaname in ('ops', 'ref', 'ingest', 'market', 'macro', 'event', 'signal', 'portfolio', 'performance')
order by schemaname, tablename;
"

if [ "$INCLUDE_SEEDS" = "1" ]; then
  echo "Seeded reference rows:"
  docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "
select 'ref.market=' || count(*) from ref.market
union all
select 'ref.exchange=' || count(*) from ref.exchange
union all
select 'ingest.data_source=' || count(*) from ingest.data_source
order by 1;
"
fi
