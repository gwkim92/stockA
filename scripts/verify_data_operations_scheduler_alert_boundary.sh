#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"

bash -n scripts/verify_data_operations_scheduler_alert_boundary.sh
"$PYTHON_BIN" -m py_compile scripts/validate_data_operations_alert_rules.py
"$PYTHON_BIN" scripts/validate_data_operations_alert_rules.py ops/observability/data-operations-alert-rules.yml

test -f ops/observability/data-operations-alert-rules.yml
test -f docs/data-operations-scheduler-alert-boundary.md
test -f docs/plans/2026-05-06-data-operations-scheduler-alert-boundary.md
test -f docs/tasks/data-operations-scheduler-alert-boundary/contract.md
test -f docs/tasks/data-operations-scheduler-alert-boundary/plan.md
test -f docs/tasks/data-operations-scheduler-alert-boundary/handoff.md
test -f docs/tasks/data-operations-scheduler-alert-boundary/review.md

grep -q "DataOperationsJobMissing" ops/observability/data-operations-alert-rules.yml
grep -q "DataOperationsJobFailed" ops/observability/data-operations-alert-rules.yml
grep -q "DataOperationsJobStale" ops/observability/data-operations-alert-rules.yml
grep -q "DataOperationsRunTimeout" ops/observability/data-operations-alert-rules.yml
grep -q "DataOperationsArtifactMissing" ops/observability/data-operations-alert-rules.yml
grep -q "DataOperationsSchedulerPreflightFailure" ops/observability/data-operations-alert-rules.yml
grep -q "Alertmanager receiver" docs/data-operations-scheduler-alert-boundary.md
grep -q "data_operations_job_health_status" docs/data-operations-scheduler-alert-boundary.md
grep -q "ops/observability/data-operations-alert-rules.yml" README.md
grep -q "data-operations-scheduler-alert-boundary" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-activation-runbook" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-operator-dry-run" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-activation-approval-gate" docs/project-execution-roadmap.md
grep -q "verify_data_operations_scheduler_alert_boundary.sh" docs/verification-plan.md
grep -q "data-operations-live-scheduler-activation-request" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-user-decision" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-final-preflight" docs/project-execution-roadmap.md
grep -q 'Current task: `manual-host-scheduler-activation-explicit-approval`' docs/project-execution-roadmap.md
grep -q '현재 고정된 immediate next task는 `manual-host-scheduler-activation-explicit-approval`' AGENTS.md

PYTHONPATH=/Users/woody/ai/agent-work-harness/src "$PYTHON_BIN" -m awh verify --repo "$ROOT_DIR" --task data-operations-scheduler-alert-boundary

echo "data operations scheduler alert boundary verification passed"
