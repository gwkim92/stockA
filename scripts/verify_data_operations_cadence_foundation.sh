#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"
REPORT_PATH=$(mktemp)
trap 'rm -f "$REPORT_PATH"' EXIT

cd "$ROOT_DIR"

bash -n scripts/verify_data_operations_cadence_foundation.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/operations/cadence.py \
  src/stockanalysis/frontend/live_adapter.py \
  src/stockanalysis/ingest/cli.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_data_operations_cadence \
  tests.test_ingest_cli.IngestCliTests.test_data_operations_cadence_cli_prints_filtered_report \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_data_health_response_matches_frontend_contract_shape \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_data_health_sql_uses_operations_cadence_registry \
  -v

PYTHONPATH=src "$PYTHON_BIN" -m stockanalysis.ingest.cli data-operations-cadence --cadence weekly > "$REPORT_PATH"
"$PYTHON_BIN" -c 'import json, sys; data = json.load(open(sys.argv[1], encoding="utf-8")); assert data["report_name"] == "data_operations_cadence_foundation"; assert data["cadence_filter"] == "weekly"; assert data["job_count"] >= 1; assert data["activation_status"] == "reference_only_not_scheduled"' "$REPORT_PATH"

test -f docs/data-operations-cadence-foundation.md
test -f docs/plans/2026-05-03-data-operations-cadence-foundation.md
test -f docs/tasks/data-operations-cadence-foundation/contract.md
test -f docs/tasks/data-operations-cadence-foundation/plan.md
test -f docs/tasks/data-operations-cadence-foundation/handoff.md
test -f docs/tasks/data-operations-cadence-foundation/review.md

grep -q "DATA_OPERATIONS_ARTIFACT_ROOT_ENV" src/stockanalysis/operations/cadence.py
grep -q "data-operations-cadence" src/stockanalysis/ingest/cli.py
grep -q "expected_jobs(" src/stockanalysis/frontend/live_adapter.py
grep -q "health_status" src/stockanalysis/frontend/live_adapter.py
grep -q "data_operations_artifact_runner" src/stockanalysis/frontend/live_adapter.py
grep -q "data-operations-cadence-foundation" docs/project-execution-roadmap.md
grep -q "data-operations-artifact-runner" docs/project-execution-roadmap.md
grep -q "data-operations-runtime-env-readiness" docs/project-execution-roadmap.md
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
grep -q "docs/data-operations-artifact-runner.md" README.md
grep -q '현재 고정된 immediate next task는 `manual-host-scheduler-activation-explicit-approval`' AGENTS.md
grep -q "verify_data_operations_cadence_foundation.sh" docs/verification-plan.md
grep -q "docs/data-operations-cadence-foundation.md" README.md

echo "data operations cadence foundation verification passed"
