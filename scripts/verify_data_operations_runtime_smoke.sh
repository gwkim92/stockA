#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
CONTAINER_NAME="${DATA_OPS_RUNTIME_SMOKE_CONTAINER_NAME:-stockanalysis-data-ops-runtime-smoke}"
POSTGRES_IMAGE="${DATA_OPS_RUNTIME_SMOKE_POSTGRES_IMAGE:-postgres:16-alpine}"
POSTGRES_DB="${DATA_OPS_RUNTIME_SMOKE_POSTGRES_DB:-stockanalysis}"
POSTGRES_USER="${DATA_OPS_RUNTIME_SMOKE_POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${DATA_OPS_RUNTIME_SMOKE_POSTGRES_PASSWORD:-postgres}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/stockanalysis-data-ops-runtime-smoke.XXXXXX")

cleanup() {
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  rm -rf "$TMP_DIR"
}

trap cleanup EXIT

cleanup
mkdir -p "$TMP_DIR"

cd "$ROOT_DIR"

bash -n scripts/smoke_data_operations_runtime.sh
bash -n scripts/verify_data_operations_runtime_smoke.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/operations/runtime_smoke.py \
  src/stockanalysis/operations/env_readiness.py \
  src/stockanalysis/operations/artifact_runner.py \
  src/stockanalysis/operations/cadence.py \
  src/stockanalysis/ingest/cli.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_data_operations_runtime_smoke \
  tests.test_data_operations_env_readiness \
  tests.test_data_operations_artifact_runner \
  -v

if scripts/smoke_data_operations_runtime.sh --env-file "$ROOT_DIR/README.md" -- "$PYTHON_BIN" -c 'print("{}")' >/tmp/stockanalysis-data-ops-runtime-smoke-readme.out 2>&1; then
  echo "Runtime smoke must refuse repo-inside env files." >&2
  exit 1
fi
grep -q "inside repository" /tmp/stockanalysis-data-ops-runtime-smoke-readme.out

ENV_FILE="$TMP_DIR/data-operations.env"
POSITIONS_CSV="$TMP_DIR/positions.csv"
ARTIFACT_ROOT="$TMP_DIR/artifacts"
SMOKE_OUTPUT="$TMP_DIR/runtime-smoke.json"

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

cat > "$POSITIONS_CSV" <<'CSV'
symbol,quantity
AAPL,10
CSV

cat > "$ENV_FILE" <<ENV
STOCKANALYSIS_PSQL_COMMAND="docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB"
STOCKANALYSIS_FRED_API_KEY="fred-runtime-token-123"
STOCKANALYSIS_ALPHA_VANTAGE_API_KEY="alpha-runtime-token-123"
STOCKANALYSIS_SEC_USER_AGENT="stockanalysis-test contact@operator.test"
STOCKANALYSIS_PORTFOLIO_POSITIONS_CSV="$POSITIONS_CSV"
STOCKANALYSIS_LLM_PROVIDER="openai"
OPENAI_API_KEY="openai-runtime-key-123456"
STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="$ARTIFACT_ROOT"
ENV
chmod 600 "$ENV_FILE"

PYTHON_BIN="$PYTHON_BIN" scripts/smoke_data_operations_runtime.sh \
  --env-file "$ENV_FILE" \
  --job-id macro-weekly \
  --timeout-seconds 120 \
  -- "$PYTHON_BIN" -m stockanalysis.ingest.cli macro-batch-upsert \
    --fixtures-dir tests/fixtures \
    --series-id CPIAUCSL \
    --series-id FEDFUNDS > "$SMOKE_OUTPUT"

"$PYTHON_BIN" - "$SMOKE_OUTPUT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["report_name"] == "data_operations_runtime_smoke"
assert payload["runtime_smoke"] == "passed"
assert payload["runtime_env_readiness"] == "passed"
assert payload["job_id"] == "macro-weekly"
assert payload["pipeline_name"] == "macro_upsert"
assert payload["artifact_run_status"] == "succeeded"
assert payload["stdout_format"] == "json"
assert payload["scheduler_activation"] == "not_activated"
artifact_dir = Path(payload["artifact_dir"])
assert (artifact_dir / "stdout.txt").exists()
assert (artifact_dir / "stdout.json").exists()
assert (artifact_dir / "stderr.log").exists()
assert (artifact_dir / "metadata.json").exists()
stdout_json = json.loads((artifact_dir / "stdout.json").read_text(encoding="utf-8"))
assert stdout_json["requested_series_count"] == 2
assert stdout_json["failed_series_count"] == 0
metadata = json.loads((artifact_dir / "metadata.json").read_text(encoding="utf-8"))
assert metadata["job_id"] == "macro-weekly"
assert metadata["status"] == "succeeded"
text = json.dumps({"payload": payload, "metadata": metadata})
for forbidden in [
    "postgresql://",
    "fred-runtime-token-123",
    "alpha-runtime-token-123",
    "openai-runtime-key-123456",
    "contact@operator.test",
]:
    assert forbidden not in text, forbidden
PY

series_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from macro.series where series_code in ('CPIAUCSL', 'FEDFUNDS');")
observation_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from macro.observation o join macro.series s on s.series_id = o.series_id where s.series_code in ('CPIAUCSL', 'FEDFUNDS');")
run_count=$(docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select count(*) from ops.pipeline_run where pipeline_name = 'macro_upsert' and status = 'succeeded';")

test "$series_count" = "2"
test "$observation_count" = "5"
test "$run_count" = "2"

test -f docs/data-operations-runtime-smoke.md
test -f docs/plans/2026-05-04-data-operations-runtime-smoke.md
test -f docs/tasks/data-operations-runtime-smoke/contract.md
test -f docs/tasks/data-operations-runtime-smoke/plan.md
test -f docs/tasks/data-operations-runtime-smoke/handoff.md
test -f docs/tasks/data-operations-runtime-smoke/review.md

grep -q "data_operations_runtime_smoke" src/stockanalysis/operations/runtime_smoke.py
grep -q "smoke_data_operations_runtime.sh" docs/data-operations-runtime-smoke.md
grep -q "data-operations-runtime-smoke" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-activation-boundary" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-install-dry-run" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-alert-boundary" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-activation-runbook" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-operator-dry-run" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-activation-approval-gate" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-request" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-user-decision" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-final-preflight" docs/project-execution-roadmap.md
grep -q "verify_data_operations_runtime_smoke.sh" docs/verification-plan.md
grep -q "docs/data-operations-runtime-smoke.md" README.md
grep -q 'Current task: `local-live-mvp-runtime`' docs/project-execution-roadmap.md
grep -q '현재 고정된 immediate next task는 `local-live-mvp-runtime`' AGENTS.md

PYTHONPATH=/Users/woody/ai/agent-work-harness/src "$PYTHON_BIN" -m awh verify --repo "$ROOT_DIR" --task data-operations-runtime-smoke

echo "data operations runtime smoke verification passed"
