#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$ROOT_DIR"

bash -n scripts/verify_data_operations_scheduler_activation_runbook.sh

test -f docs/data-operations-scheduler-activation-runbook.md
test -f docs/plans/2026-05-06-data-operations-scheduler-activation-runbook.md
test -f docs/tasks/data-operations-scheduler-activation-runbook/contract.md
test -f docs/tasks/data-operations-scheduler-activation-runbook/plan.md
test -f docs/tasks/data-operations-scheduler-activation-runbook/handoff.md
test -f docs/tasks/data-operations-scheduler-activation-runbook/review.md

grep -q "manual approval" docs/data-operations-scheduler-activation-runbook.md
grep -q "scripts/check_data_operations_runtime_env.sh" docs/data-operations-scheduler-activation-runbook.md
grep -q "scripts/run_data_operations_scheduler_job.sh" docs/data-operations-scheduler-activation-runbook.md
grep -q "scripts/render_data_operations_scheduler_install.sh" docs/data-operations-scheduler-activation-runbook.md
grep -q "ops/observability/data-operations-alert-rules.yml" docs/data-operations-scheduler-activation-runbook.md
grep -q "launchctl bootstrap" docs/data-operations-scheduler-activation-runbook.md
grep -q "launchctl bootout" docs/data-operations-scheduler-activation-runbook.md
grep -q "Evidence Checklist" docs/data-operations-scheduler-activation-runbook.md
grep -q "Stop Conditions" docs/data-operations-scheduler-activation-runbook.md
grep -q "reference-only" docs/data-operations-scheduler-activation-runbook.md
grep -q "data-operations-scheduler-operator-dry-run" docs/data-operations-scheduler-activation-runbook.md

if grep -Eq "launchctl|Library/LaunchAgents" \
  scripts/run_data_operations_scheduler_job.sh \
  scripts/render_data_operations_scheduler_install.sh; then
  echo "Data operations scheduler runtime/render scripts must not mutate host launchd state." >&2
  exit 1
fi

grep -q "data-operations-scheduler-activation-runbook" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-operator-dry-run" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-activation-approval-gate" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-request" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-user-decision" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-final-preflight" docs/project-execution-roadmap.md
grep -q 'Current task: `local-live-mvp-runtime`' docs/project-execution-roadmap.md
grep -q '현재 고정된 immediate next task는 `local-live-mvp-runtime`' AGENTS.md
grep -q "docs/data-operations-scheduler-activation-runbook.md" README.md
grep -q "verify_data_operations_scheduler_activation_runbook.sh" docs/verification-plan.md

PYTHONPATH=/Users/woody/ai/agent-work-harness/src "$PYTHON_BIN" -m awh verify --repo "$ROOT_DIR" --task data-operations-scheduler-activation-runbook

echo "data operations scheduler activation runbook verification passed"
