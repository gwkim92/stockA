#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

bash -n scripts/verify_operating_data_orchestrator.sh
python3 -m compileall \
  src/stockanalysis/operations/operating_data_orchestrator.py \
  src/stockanalysis/operations/artifact_runner.py \
  src/stockanalysis/operations/cli.py \
  src/stockanalysis/frontend/live_adapter.py \
  tests/test_operating_data_orchestrator.py \
  tests/test_data_operations_artifact_runner.py \
  tests/test_data_operations_cli.py \
  tests/test_frontend_live_adapter.py >/dev/null

PYTHONPATH=src python3 -m unittest \
  tests.test_operating_data_orchestrator \
  tests.test_data_operations_artifact_runner.DataOperationsArtifactRunnerTests.test_runner_passes_env_to_child_process_without_recording_it \
  tests.test_data_operations_cli.DataOperationsCliTests.test_operating_data_run_command_writes_repo_outside_output \
  tests.test_data_operations_cli.DataOperationsCliTests.test_operating_data_run_output_rejects_repo_inside_path \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_data_health_sql_uses_operations_cadence_registry

TMP_ROOT=$(mktemp -d /tmp/stockanalysis-operating-data.XXXXXX)
trap 'rm -rf "$TMP_ROOT"' EXIT

mkdir -p "$TMP_ROOT/artifacts" "$TMP_ROOT/runtime"
cat >"$TMP_ROOT/positions.csv" <<EOF
symbol,quantity,cost_basis
AAPL,10,150
TSLA,2,250
EOF

cat >"$TMP_ROOT/data-operations.env" <<EOF
STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="$TMP_ROOT/artifacts"
STOCKANALYSIS_PORTFOLIO_POSITIONS_CSV="$TMP_ROOT/positions.csv"
STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH="$TMP_ROOT/ledger.json"
STOCKANALYSIS_MARKET_PRICE_PROVIDER="twelve_data"
EOF

PYTHONPATH=src python3 -m stockanalysis.operations.cli operating-data-run \
  --repo-root "$ROOT_DIR" \
  --runtime-root "$TMP_ROOT/runtime" \
  --data-operations-env-file "$TMP_ROOT/data-operations.env" \
  --output "$TMP_ROOT/operating-data-run.json" >/dev/null

python3 - "$TMP_ROOT/operating-data-run.json" <<'PY'
import json
import sys

path = sys.argv[1]
text = open(path, encoding="utf-8").read()
report = json.loads(text)

assert report["report_name"] == "operating_data_run"
assert report["run_status"] == "preview_not_executed"
assert report["execute"] is False
assert report["broker_submission_allowed"] is False
assert report["scheduler_mutation_allowed"] is False
assert "missing-symbol-price-backfill" == report["planned_steps"][0]["step_id"]
assert "portfolio-position-snapshot" in [step["step_id"] for step in report["planned_steps"]]
assert "paper-validation-audit" in [step["step_id"] for step in report["planned_steps"]]
assert "postgresql://" not in text
assert "api-key" not in text.lower()
print("operating data orchestrator verification passed")
PY

test -f docs/tasks/operating-data-orchestrator/contract.md
test -f docs/tasks/operating-data-orchestrator/handoff.md
test -f docs/plans/2026-05-20-operating-data-orchestrator.md
