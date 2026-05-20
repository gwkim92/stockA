#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

bash -n scripts/verify_local_ingest_worker_loop.sh
python3 -m compileall src/stockanalysis/operations/local_ingest_worker.py src/stockanalysis/operations/cli.py tests/test_local_ingest_worker.py tests/test_data_operations_cli.py >/dev/null
PYTHONPATH=src python3 -m unittest \
  tests.test_local_ingest_worker \
  tests.test_data_operations_cli.DataOperationsCliTests.test_local_ingest_worker_run_command_passes_runtime_args_and_writes_output \
  tests.test_data_operations_cli.DataOperationsCliTests.test_local_ingest_worker_run_rejects_repo_inside_output

TMP_ROOT=$(mktemp -d /tmp/stockanalysis-local-ingest-worker.XXXXXX)
trap 'rm -rf "$TMP_ROOT"' EXIT

mkdir -p "$TMP_ROOT/artifacts"
cat >"$TMP_ROOT/data-operations.env" <<EOF
STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="$TMP_ROOT/artifacts"
EOF
: >"$TMP_ROOT/frontend-api.env"

PYTHONPATH=src python3 -m stockanalysis.operations.cli local-ingest-worker-run \
  --repo-root "$ROOT_DIR" \
  --runtime-root "$TMP_ROOT" \
  --job-id market-price-daily \
  --python-executable /usr/bin/python3 \
  --smoke-output "$TMP_ROOT/manual-local-ingest-smoke.json" \
  --output "$TMP_ROOT/local-ingest-worker.json" >/dev/null

python3 - "$TMP_ROOT/local-ingest-worker.json" "$TMP_ROOT/manual-local-ingest-smoke.json" <<'PY'
import json
import sys

worker = json.load(open(sys.argv[1], encoding="utf-8"))
smoke = json.load(open(sys.argv[2], encoding="utf-8"))

assert worker["report_name"] == "local_ingest_worker"
assert worker["worker_status"] == "preview_not_executed"
assert worker["execute"] is False
assert worker["completed_cycle_count"] == 1
assert worker["codex_host_mutation_allowed"] is False
assert worker["launchagents_install_allowed"] is False
assert smoke["report_name"] == "manual_local_ingest_smoke"
assert smoke["smoke_status"] == "preview_not_executed"
print("local ingest worker loop verification passed")
PY
