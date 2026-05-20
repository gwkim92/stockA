#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/stockanalysis-data-ops-host-execution.XXXXXX")
trap 'rm -rf "$TMP_DIR"' EXIT

cd "$ROOT_DIR"

bash -n scripts/run_data_operations_live_scheduler_host_activation_execution.sh
bash -n scripts/verify_data_operations_live_scheduler_host_activation_execution.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/operations/cli.py \
  src/stockanalysis/operations/path_policy.py \
  src/stockanalysis/operations/report_io.py \
  src/stockanalysis/operations/scheduler_activation_execution.py \
  src/stockanalysis/operations/scheduler_activation_execution_final_preflight.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_data_operations_scheduler_activation_execution \
  tests.test_data_operations_scheduler_activation_execution_final_preflight \
  -v

if grep -Eq '^[[:space:]]*launchctl[[:space:]]' scripts/run_data_operations_live_scheduler_host_activation_execution.sh; then
  echo "Host activation execution wrapper must not execute launchctl." >&2
  exit 1
fi
grep -q 'stockanalysis.operations.cli' scripts/run_data_operations_live_scheduler_host_activation_execution.sh
grep -q 'host-activation-execution' src/stockanalysis/operations/cli.py

FINAL_PREFLIGHT_JSON="$TMP_DIR/execution-final-preflight.json"
MISSING_REPORT="$TMP_DIR/missing-confirmation-report.json"
CONFIRM_RECORD="$TMP_DIR/confirm-host-activation-execution.json"
ABORT_RECORD="$TMP_DIR/abort-host-activation-execution.json"
BAD_RECORD="$TMP_DIR/bad-confirmation.json"
SECRET_RECORD="$TMP_DIR/secret-confirmation.json"
CONFIRM_REPORT="$TMP_DIR/confirm-report.json"
ABORT_REPORT="$TMP_DIR/abort-report.json"

"$PYTHON_BIN" - \
  "$FINAL_PREFLIGHT_JSON" \
  "$CONFIRM_RECORD" \
  "$ABORT_RECORD" \
  "$BAD_RECORD" \
  "$SECRET_RECORD" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

final_preflight_path = Path(sys.argv[1])
confirm_path = Path(sys.argv[2])
abort_path = Path(sys.argv[3])
bad_path = Path(sys.argv[4])
secret_path = Path(sys.argv[5])

final_preflight = {
    "report_name": "data_operations_live_scheduler_host_activation_execution_final_preflight",
    "execution_final_preflight": "passed_ready_for_host_activation_execution_task",
    "host_activation_execution_allowed_for_next_task": True,
    "host_activation_execution_allowed_in_this_task": False,
    "scheduler_activation": "not_installed",
    "host_install_path_written": False,
    "launchctl_executed": False,
    "child_command_executed": False,
    "job_id": "macro-weekly",
    "pipeline_name": "Macro Weekly",
    "domain": "macro",
    "cadence": "weekly",
    "rendered_label": "com.stockanalysis.data-operations.macro-weekly",
    "host_plist_path_preview": "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist",
    "execution_command_preview": [
        'install -m 600 "/tmp/rendered.plist" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
        'launchctl bootstrap "gui/$(id -u)" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
    ],
    "rollback_command_preview": [
        'launchctl bootout "gui/$(id -u)" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
    ],
    "manual_next_step": "data-operations-live-scheduler-host-activation-execution",
}
final_preflight_path.write_text(json.dumps(final_preflight, indent=2, sort_keys=True) + "\n", encoding="utf-8")

base = {
    "confirmation_record": "data_operations_live_scheduler_host_activation_execution_confirmation",
    "confirmer": "operator-handle",
    "confirmed_at": "2026-05-15T09:00:00Z",
    "job_id": "macro-weekly",
    "execution_final_preflight_report": str(final_preflight_path),
    "confirmation_scope": "data_operations_scheduler_host_activation_execution",
    "acknowledged_final_preflight_state": "passed_ready_for_host_activation_execution_task",
    "acknowledged_mutation_boundary": [
        "host_launchagents_write",
        "launchctl_bootstrap",
        "launchctl_kickstart",
        "launchctl_print",
        "rollback_required_if_activation_fails",
        "recurring_data_operation_execution",
    ],
    "operator_note": "fixture confirmation",
}
confirm_path.write_text(
    json.dumps({**base, "confirmation": "confirm_host_activation_execution"}, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
abort_path.write_text(
    json.dumps({**base, "confirmation": "abort_host_activation_execution"}, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
bad_path.write_text(
    json.dumps(
        {
            **base,
            "confirmation": "confirm_host_activation_execution",
            "execution_final_preflight_report": str(final_preflight_path.with_name("wrong-final-preflight.json")),
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
            "confirmation": "confirm_host_activation_execution",
            "operator_note": "postgresql://user:pass@host/db",
        },
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)
PY

scripts/run_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-final-preflight-report "$FINAL_PREFLIGHT_JSON" \
  --output "$MISSING_REPORT" >/dev/null

scripts/run_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-final-preflight-report "$FINAL_PREFLIGHT_JSON" \
  --confirmation-record "$CONFIRM_RECORD" \
  --output "$CONFIRM_REPORT" >/dev/null

scripts/run_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-final-preflight-report "$FINAL_PREFLIGHT_JSON" \
  --confirmation-record "$ABORT_RECORD" \
  --output "$ABORT_REPORT" >/dev/null

"$PYTHON_BIN" - "$MISSING_REPORT" "$CONFIRM_REPORT" "$ABORT_REPORT" "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

missing = json.load(open(sys.argv[1], encoding="utf-8"))
confirm = json.load(open(sys.argv[2], encoding="utf-8"))
abort = json.load(open(sys.argv[3], encoding="utf-8"))
repo_root = Path(sys.argv[4]).resolve()

assert missing["execution_gate"] == "blocked_pending_explicit_host_mutation_confirmation"
assert missing["host_activation_execution_allowed_in_this_task"] is False
assert missing["host_activation_execution_allowed_for_manual_operator"] is False
assert missing["launchctl_executed"] is False
assert missing["host_install_path_written"] is False

assert confirm["execution_gate"] == "confirmed_for_manual_host_mutation_not_executed_by_this_task"
assert confirm["host_activation_execution_allowed_in_this_task"] is False
assert confirm["host_activation_execution_allowed_for_manual_operator"] is True
assert confirm["launchctl_executed"] is False
assert confirm["host_install_path_written"] is False
assert confirm["host_activation_execution_performed"] is False
assert confirm["manual_next_step"] == "manual-host-scheduler-activation"
assert not Path(confirm["execution_final_preflight_report_path"]).resolve().is_relative_to(repo_root)

assert abort["execution_gate"] == "aborted_by_explicit_host_mutation_confirmation"
assert abort["host_activation_execution_allowed_for_manual_operator"] is False
assert abort["manual_next_step"] == "data-operations-live-scheduler-host-activation-execution-final-preflight"

text = json.dumps([missing, confirm, abort])
assert "postgresql://" not in text
PY

if scripts/run_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-final-preflight-report "$FINAL_PREFLIGHT_JSON" \
  --confirmation-record "$BAD_RECORD" \
  --output "$TMP_DIR/bad-report.json" >/tmp/stockanalysis-host-execution-bad.out 2>&1; then
  echo "Host activation execution must reject mismatched confirmation records." >&2
  exit 1
fi
grep -q "same execution final preflight report path" /tmp/stockanalysis-host-execution-bad.out

if scripts/run_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-final-preflight-report "$FINAL_PREFLIGHT_JSON" \
  --confirmation-record "$SECRET_RECORD" \
  --output "$TMP_DIR/secret-report.json" >/tmp/stockanalysis-host-execution-secret.out 2>&1; then
  echo "Host activation execution must reject secret-like confirmation records." >&2
  exit 1
fi
grep -q "secret-like" /tmp/stockanalysis-host-execution-secret.out

if scripts/run_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-final-preflight-report "$ROOT_DIR/README.md" \
  --output "$TMP_DIR/readme-report.json" >/tmp/stockanalysis-host-execution-readme.out 2>&1; then
  echo "Host activation execution must refuse repo-inside final preflight reports." >&2
  exit 1
fi
grep -q "outside repository" /tmp/stockanalysis-host-execution-readme.out

if scripts/run_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-final-preflight-report "$FINAL_PREFLIGHT_JSON" \
  --confirmation-record "$ROOT_DIR/README.md" \
  --output "$TMP_DIR/readme-confirmation-report.json" >/tmp/stockanalysis-host-execution-confirmation.out 2>&1; then
  echo "Host activation execution must refuse repo-inside confirmation records." >&2
  exit 1
fi
grep -q "outside repository" /tmp/stockanalysis-host-execution-confirmation.out

if scripts/run_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-final-preflight-report "$FINAL_PREFLIGHT_JSON" \
  --output "$ROOT_DIR/tmp-host-activation-execution.json" >/tmp/stockanalysis-host-execution-output.out 2>&1; then
  echo "Host activation execution must refuse repo-inside output paths." >&2
  exit 1
fi
grep -q "outside repository" /tmp/stockanalysis-host-execution-output.out

test -f docs/data-operations-live-scheduler-host-activation-execution.md
test -f docs/plans/2026-05-15-data-operations-live-scheduler-host-activation-execution.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution/contract.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution/plan.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution/handoff.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution/review.md

grep -q "run_data_operations_live_scheduler_host_activation_execution.sh" docs/data-operations-live-scheduler-host-activation-execution.md
grep -q "blocked_pending_explicit_host_mutation_confirmation" docs/data-operations-live-scheduler-host-activation-execution.md
grep -q "confirmed_for_manual_host_mutation_not_executed_by_this_task" docs/data-operations-live-scheduler-host-activation-execution.md
grep -q "data-operations-live-scheduler-host-activation-execution" docs/project-execution-roadmap.md
grep -q 'Current task: `manual-host-scheduler-activation-explicit-approval`' docs/project-execution-roadmap.md
grep -q '현재 고정된 immediate next task는 `manual-host-scheduler-activation-explicit-approval`' AGENTS.md
grep -q "verify_data_operations_live_scheduler_host_activation_execution.sh" docs/verification-plan.md
grep -q "docs/data-operations-live-scheduler-host-activation-execution.md" README.md

PYTHONPATH=/Users/woody/ai/agent-work-harness/src "$PYTHON_BIN" -m awh verify --repo "$ROOT_DIR" --task data-operations-live-scheduler-host-activation-execution

echo "data operations live scheduler host activation execution verification passed"
