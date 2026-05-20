#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/stockanalysis-manual-host-approval.XXXXXX")
trap 'rm -rf "$TMP_DIR"' EXIT

cd "$ROOT_DIR"

bash -n scripts/prepare_manual_host_scheduler_activation_explicit_approval.sh
bash -n scripts/verify_manual_host_scheduler_activation_explicit_approval.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/operations/cli.py \
  src/stockanalysis/operations/manual_host_scheduler_activation_approval.py \
  src/stockanalysis/operations/path_policy.py \
  src/stockanalysis/operations/report_io.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_manual_host_scheduler_activation_approval \
  tests.test_data_operations_cli \
  -v

if grep -Eq '^[[:space:]]*launchctl[[:space:]]' scripts/prepare_manual_host_scheduler_activation_explicit_approval.sh; then
  echo "Manual host scheduler activation approval wrapper must not execute launchctl." >&2
  exit 1
fi
grep -q 'stockanalysis.operations.cli' scripts/prepare_manual_host_scheduler_activation_explicit_approval.sh
grep -q 'manual-host-scheduler-activation-explicit-approval' src/stockanalysis/operations/cli.py

HOST_EXECUTION_REPORT="$TMP_DIR/host-activation-execution.json"
MISSING_REPORT="$TMP_DIR/missing-approval-report.json"
APPROVAL_RECORD="$TMP_DIR/approve-manual-host-scheduler-activation.json"
ABORT_RECORD="$TMP_DIR/abort-manual-host-scheduler-activation.json"
DRIFT_RECORD="$TMP_DIR/drift-manual-host-scheduler-activation.json"
SECRET_RECORD="$TMP_DIR/secret-manual-host-scheduler-activation.json"
APPROVED_REPORT="$TMP_DIR/approved-report.json"
ABORT_REPORT="$TMP_DIR/abort-report.json"

"$PYTHON_BIN" - \
  "$HOST_EXECUTION_REPORT" \
  "$APPROVAL_RECORD" \
  "$ABORT_RECORD" \
  "$DRIFT_RECORD" \
  "$SECRET_RECORD" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

host_execution_path = Path(sys.argv[1])
approval_path = Path(sys.argv[2])
abort_path = Path(sys.argv[3])
drift_path = Path(sys.argv[4])
secret_path = Path(sys.argv[5])
execution_commands = [
    'install -m 600 "/tmp/rendered.plist" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
    'launchctl bootstrap "gui/$(id -u)" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
    'launchctl kickstart -k "gui/$(id -u)/com.stockanalysis.data-operations.macro-weekly"',
    'launchctl print "gui/$(id -u)/com.stockanalysis.data-operations.macro-weekly"',
]
rollback_commands = [
    'launchctl bootout "gui/$(id -u)" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
    'launchctl print "gui/$(id -u)/com.stockanalysis.data-operations.macro-weekly"',
]
host_execution = {
    "report_name": "data_operations_live_scheduler_host_activation_execution",
    "execution_gate": "confirmed_for_manual_host_mutation_not_executed_by_this_task",
    "host_activation_execution_allowed_in_this_task": False,
    "host_activation_execution_allowed_for_manual_operator": True,
    "scheduler_activation": "not_installed",
    "host_install_path_written": False,
    "launchctl_executed": False,
    "child_command_executed": False,
    "host_activation_execution_performed": False,
    "job_id": "macro-weekly",
    "pipeline_name": "Macro Weekly",
    "domain": "macro",
    "cadence": "weekly",
    "rendered_label": "com.stockanalysis.data-operations.macro-weekly",
    "host_plist_path_preview": "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist",
    "execution_command_preview": execution_commands,
    "rollback_command_preview": rollback_commands,
    "manual_next_step": "manual-host-scheduler-activation",
}
host_execution_path.write_text(json.dumps(host_execution, indent=2, sort_keys=True) + "\n", encoding="utf-8")

base = {
    "approval_record": "manual_host_scheduler_activation_explicit_approval",
    "approver": "operator-handle",
    "approved_at": "2026-05-15T09:30:00Z",
    "job_id": "macro-weekly",
    "host_activation_execution_report": str(host_execution_path),
    "approval_scope": "manual_host_scheduler_activation",
    "acknowledged_execution_gate": "confirmed_for_manual_host_mutation_not_executed_by_this_task",
    "approved_exact_execution_commands": execution_commands,
    "approved_exact_rollback_commands": rollback_commands,
    "acknowledged_mutation_boundary": [
        "host_launchagents_write",
        "launchctl_bootstrap",
        "launchctl_kickstart",
        "launchctl_print",
        "rollback_required_if_activation_fails",
        "recurring_data_operation_execution",
    ],
    "acknowledged_operator_responsibility": [
        "operator_runs_commands_outside_codex",
        "operator_records_exit_statuses",
        "operator_collects_launchctl_print_evidence",
        "operator_collects_first_run_artifacts",
        "operator_can_execute_rollback",
    ],
    "operator_note": "fixture approval",
}
approval_path.write_text(
    json.dumps({**base, "approval": "approve_exact_host_scheduler_activation"}, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
abort_path.write_text(
    json.dumps({**base, "approval": "abort_exact_host_scheduler_activation"}, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
drift_path.write_text(
    json.dumps(
        {
            **base,
            "approval": "approve_exact_host_scheduler_activation",
            "approved_exact_execution_commands": ["launchctl bootstrap gui/501 /tmp/wrong.plist"],
        },
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)
secret_path.write_text(
    json.dumps(
        {
            **base,
            "approval": "approve_exact_host_scheduler_activation",
            "operator_note": "postgresql://user:pass@host/db",
        },
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)
PY

scripts/prepare_manual_host_scheduler_activation_explicit_approval.sh \
  --host-activation-execution-report "$HOST_EXECUTION_REPORT" \
  --output "$MISSING_REPORT" >/dev/null

scripts/prepare_manual_host_scheduler_activation_explicit_approval.sh \
  --host-activation-execution-report "$HOST_EXECUTION_REPORT" \
  --approval-record "$APPROVAL_RECORD" \
  --output "$APPROVED_REPORT" >/dev/null

scripts/prepare_manual_host_scheduler_activation_explicit_approval.sh \
  --host-activation-execution-report "$HOST_EXECUTION_REPORT" \
  --approval-record "$ABORT_RECORD" \
  --output "$ABORT_REPORT" >/dev/null

"$PYTHON_BIN" - "$MISSING_REPORT" "$APPROVED_REPORT" "$ABORT_REPORT" "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

missing = json.load(open(sys.argv[1], encoding="utf-8"))
approved = json.load(open(sys.argv[2], encoding="utf-8"))
abort = json.load(open(sys.argv[3], encoding="utf-8"))
repo_root = Path(sys.argv[4]).resolve()

assert missing["approval_gate"] == "blocked_pending_exact_host_command_approval"
assert missing["host_activation_allowed_for_manual_operator"] is False
assert missing["codex_host_mutation_allowed"] is False
assert missing["launchctl_executed"] is False
assert missing["host_install_path_written"] is False
assert missing["approval_record_template"]["approved_exact_execution_commands"] == missing["exact_execution_commands"]

assert approved["approval_gate"] == "approved_for_manual_operator_host_activation_not_executed_by_codex"
assert approved["host_activation_allowed_for_manual_operator"] is True
assert approved["codex_host_mutation_allowed"] is False
assert approved["launchctl_executed"] is False
assert approved["host_install_path_written"] is False
assert approved["host_activation_execution_performed"] is False
assert approved["manual_next_step"] == "manual-host-scheduler-activation-operator-evidence"
assert not Path(approved["host_activation_execution_report_path"]).resolve().is_relative_to(repo_root)

assert abort["approval_gate"] == "aborted_manual_host_scheduler_activation"
assert abort["host_activation_allowed_for_manual_operator"] is False
assert abort["manual_next_step"] == "data-operations-live-scheduler-host-activation-execution-final-preflight"

text = json.dumps([missing, approved, abort])
assert "postgresql://" not in text
PY

if scripts/prepare_manual_host_scheduler_activation_explicit_approval.sh \
  --host-activation-execution-report "$HOST_EXECUTION_REPORT" \
  --approval-record "$DRIFT_RECORD" \
  --output "$TMP_DIR/drift-report.json" >/tmp/stockanalysis-manual-host-approval-drift.out 2>&1; then
  echo "Manual host scheduler activation approval must reject exact command drift." >&2
  exit 1
fi
grep -q "exact execution commands" /tmp/stockanalysis-manual-host-approval-drift.out

if scripts/prepare_manual_host_scheduler_activation_explicit_approval.sh \
  --host-activation-execution-report "$HOST_EXECUTION_REPORT" \
  --approval-record "$SECRET_RECORD" \
  --output "$TMP_DIR/secret-report.json" >/tmp/stockanalysis-manual-host-approval-secret.out 2>&1; then
  echo "Manual host scheduler activation approval must reject secret-like approval records." >&2
  exit 1
fi
grep -q "secret-like" /tmp/stockanalysis-manual-host-approval-secret.out

if scripts/prepare_manual_host_scheduler_activation_explicit_approval.sh \
  --host-activation-execution-report "$ROOT_DIR/README.md" \
  --output "$TMP_DIR/readme-report.json" >/tmp/stockanalysis-manual-host-approval-readme.out 2>&1; then
  echo "Manual host scheduler activation approval must refuse repo-inside host activation execution reports." >&2
  exit 1
fi
grep -q "outside repository" /tmp/stockanalysis-manual-host-approval-readme.out

if scripts/prepare_manual_host_scheduler_activation_explicit_approval.sh \
  --host-activation-execution-report "$HOST_EXECUTION_REPORT" \
  --approval-record "$ROOT_DIR/README.md" \
  --output "$TMP_DIR/readme-approval-report.json" >/tmp/stockanalysis-manual-host-approval-record.out 2>&1; then
  echo "Manual host scheduler activation approval must refuse repo-inside approval records." >&2
  exit 1
fi
grep -q "outside repository" /tmp/stockanalysis-manual-host-approval-record.out

if scripts/prepare_manual_host_scheduler_activation_explicit_approval.sh \
  --host-activation-execution-report "$HOST_EXECUTION_REPORT" \
  --output "$ROOT_DIR/tmp-manual-host-activation-approval.json" >/tmp/stockanalysis-manual-host-approval-output.out 2>&1; then
  echo "Manual host scheduler activation approval must refuse repo-inside output paths." >&2
  exit 1
fi
grep -q "outside repository" /tmp/stockanalysis-manual-host-approval-output.out

test -f docs/manual-host-scheduler-activation-explicit-approval.md
test -f docs/plans/2026-05-15-manual-host-scheduler-activation-explicit-approval.md
test -f docs/tasks/manual-host-scheduler-activation-explicit-approval/contract.md
test -f docs/tasks/manual-host-scheduler-activation-explicit-approval/plan.md
test -f docs/tasks/manual-host-scheduler-activation-explicit-approval/handoff.md
test -f docs/tasks/manual-host-scheduler-activation-explicit-approval/review.md

grep -q "prepare_manual_host_scheduler_activation_explicit_approval.sh" docs/manual-host-scheduler-activation-explicit-approval.md
grep -q "blocked_pending_exact_host_command_approval" docs/manual-host-scheduler-activation-explicit-approval.md
grep -q "approved_for_manual_operator_host_activation_not_executed_by_codex" docs/manual-host-scheduler-activation-explicit-approval.md
grep -q "manual-host-scheduler-activation-explicit-approval" docs/project-execution-roadmap.md
grep -q 'Current task: `local-live-mvp-runtime`' docs/project-execution-roadmap.md
grep -q '현재 고정된 immediate next task는 `local-live-mvp-runtime`' AGENTS.md
grep -q "verify_manual_host_scheduler_activation_explicit_approval.sh" docs/verification-plan.md
grep -q "docs/manual-host-scheduler-activation-explicit-approval.md" README.md

PYTHONPATH=/Users/woody/ai/agent-work-harness/src "$PYTHON_BIN" -m awh verify --repo "$ROOT_DIR" --task manual-host-scheduler-activation-explicit-approval

echo "manual host scheduler activation explicit approval verification passed"
