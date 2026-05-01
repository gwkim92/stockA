#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
CONTAINER_NAME="${MACRO_REPORT_VERIFY_CONTAINER_NAME:-stockanalysis-macro-report-verify}"
POSTGRES_IMAGE="${MACRO_REPORT_VERIFY_POSTGRES_IMAGE:-postgres:16-alpine}"
POSTGRES_DB="${MACRO_REPORT_VERIFY_POSTGRES_DB:-stockanalysis}"
POSTGRES_USER="${MACRO_REPORT_VERIFY_POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${MACRO_REPORT_VERIFY_POSTGRES_PASSWORD:-postgres}"
REPORT_PATH="${TMPDIR:-/tmp}/stockanalysis-macro-run-history.json"

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

STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli macro-run-history \
  --limit 5 > "$REPORT_PATH"

python3 - "$REPORT_PATH" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

assert payload["pipeline_name"] == "macro_upsert"
assert payload["run_count"] == 2
assert payload["status_counts"]["succeeded"] == 2
assert len(payload["runs"]) == 2
series_ids = {item["series_id"] for item in payload["runs"]}
assert series_ids == {"CPIAUCSL", "FEDFUNDS"}
observation_counts = sorted(item["observation_count"] for item in payload["runs"])
assert observation_counts == [2, 3]
PY
