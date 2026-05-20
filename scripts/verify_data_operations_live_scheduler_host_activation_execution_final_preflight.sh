#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/stockanalysis-data-ops-execution-final-preflight.XXXXXX")
trap 'rm -rf "$TMP_DIR"' EXIT

cd "$ROOT_DIR"

bash -n scripts/preflight_data_operations_live_scheduler_host_activation_execution.sh
bash -n scripts/verify_data_operations_live_scheduler_host_activation_execution_final_preflight.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/operations/cli.py \
  src/stockanalysis/operations/env_file.py \
  src/stockanalysis/operations/path_policy.py \
  src/stockanalysis/operations/report_io.py \
  src/stockanalysis/operations/scheduler_activation_execution_final_preflight.py \
  src/stockanalysis/operations/scheduler_activation_execution_decision.py \
  src/stockanalysis/operations/scheduler_activation_execution_request.py \
  src/stockanalysis/operations/scheduler_activation_host_plan.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_data_operations_scheduler_activation_execution_final_preflight \
  tests.test_data_operations_scheduler_activation_execution_decision \
  tests.test_data_operations_cli \
  -v

if grep -Eq '^[[:space:]]*launchctl[[:space:]]' scripts/preflight_data_operations_live_scheduler_host_activation_execution.sh; then
  echo "Host activation execution final preflight script must not execute launchctl." >&2
  exit 1
fi
grep -q 'stockanalysis.operations.cli' scripts/preflight_data_operations_live_scheduler_host_activation_execution.sh
grep -q 'host-activation-execution-final-preflight' src/stockanalysis/operations/cli.py

ENV_FILE="$TMP_DIR/data-operations.env"
BAD_ENV_FILE="$TMP_DIR/bad-data-operations.env"
POSITIONS_CSV="$TMP_DIR/positions.csv"
ARTIFACT_ROOT="$TMP_DIR/artifacts"
HOST_PLAN_JSON="$TMP_DIR/host-activation-plan.json"
EXECUTION_REQUEST_JSON="$TMP_DIR/host-activation-execution-request.json"
APPROVE_EXECUTION_DECISION_REPORT="$TMP_DIR/approve-execution-decision-report.json"
DENY_EXECUTION_DECISION_REPORT="$TMP_DIR/deny-execution-decision-report.json"
APPROVE_OUTPUT_DIR="$TMP_DIR/approve-execution-final-preflight"
DENY_OUTPUT_DIR="$TMP_DIR/deny-execution-final-preflight"
BAD_ENV_OUTPUT_DIR="$TMP_DIR/bad-env-execution-final-preflight"
DRIFT_HOST_PLAN_JSON="$TMP_DIR/drift-host-activation-plan.json"
DRIFT_EXECUTION_REQUEST_JSON="$TMP_DIR/drift-host-activation-execution-request.json"
DRIFT_DECISION_REPORT="$TMP_DIR/drift-approve-execution-decision-report.json"

cat > "$POSITIONS_CSV" <<'CSV'
symbol,quantity
AAPL,10
CSV

cat > "$ENV_FILE" <<ENV
STOCKANALYSIS_DATABASE_URL="postgresql://execution_final_user:execution_final_pass@db.internal:5432/stockanalysis"
STOCKANALYSIS_FRED_API_KEY="fred-execution-final-token-123"
STOCKANALYSIS_ALPHA_VANTAGE_API_KEY="alpha-execution-final-token-123"
STOCKANALYSIS_SEC_USER_AGENT="stockanalysis-execution-final operator@test.invalid"
STOCKANALYSIS_PORTFOLIO_POSITIONS_CSV="$POSITIONS_CSV"
STOCKANALYSIS_LLM_PROVIDER="openai"
OPENAI_API_KEY="openai-execution-final-key-123456"
STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="$ARTIFACT_ROOT"
ENV
chmod 600 "$ENV_FILE"

cat > "$BAD_ENV_FILE" <<ENV
STOCKANALYSIS_DATABASE_URL="postgresql://execution_final_user:execution_final_pass@db.internal:5432/stockanalysis"
STOCKANALYSIS_FRED_API_KEY="fred-execution-final-token-123"
ENV
chmod 600 "$BAD_ENV_FILE"

"$PYTHON_BIN" - \
  "$HOST_PLAN_JSON" \
  "$EXECUTION_REQUEST_JSON" \
  "$APPROVE_EXECUTION_DECISION_REPORT" \
  "$DENY_EXECUTION_DECISION_REPORT" \
  "$DRIFT_HOST_PLAN_JSON" \
  "$DRIFT_EXECUTION_REQUEST_JSON" \
  "$DRIFT_DECISION_REPORT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

host_plan_path = Path(sys.argv[1])
execution_request_path = Path(sys.argv[2])
approve_decision_path = Path(sys.argv[3])
deny_decision_path = Path(sys.argv[4])
drift_host_plan_path = Path(sys.argv[5])
drift_request_path = Path(sys.argv[6])
drift_decision_path = Path(sys.argv[7])

host_plan = {
    "report_name": "data_operations_live_scheduler_host_activation_plan",
    "host_activation_plan": "ready_for_execution_request",
    "activation_allowed_for_execution_request": True,
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
    "execution_plan_steps": [
        {
            "order": 1,
            "command_preview": 'install -m 600 "/tmp/rendered.plist" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
            "execution_status": "not_executed",
        },
        {
            "order": 2,
            "command_preview": 'launchctl bootstrap "gui/$(id -u)" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
            "execution_status": "not_executed",
        },
    ],
    "rollback_plan_steps": [
        {
            "order": 1,
            "command_preview": 'launchctl bootout "gui/$(id -u)" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
            "execution_status": "not_executed",
        }
    ],
    "manual_next_step": "data-operations-live-scheduler-host-activation-execution-request",
}
host_plan_path.write_text(json.dumps(host_plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")

execution_request = {
    "report_name": "data_operations_live_scheduler_host_activation_execution_request",
    "execution_request": "pending_explicit_execution_approval",
    "requested_user_decision_values": [
        "approve_host_activation_execution",
        "deny_host_activation_execution",
    ],
    "requires_explicit_execution_approval": True,
    "execution_allowed_by_plan": True,
    "scheduler_activation": "not_installed",
    "host_install_path_written": False,
    "launchctl_executed": False,
    "child_command_executed": False,
    "host_activation_execution_allowed_in_this_task": False,
    "job_id": "macro-weekly",
    "pipeline_name": "Macro Weekly",
    "domain": "macro",
    "cadence": "weekly",
    "rendered_label": "com.stockanalysis.data-operations.macro-weekly",
    "host_plist_path_preview": "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist",
    "host_activation_plan_report_path": str(host_plan_path),
    "execution_command_preview": [step["command_preview"] for step in host_plan["execution_plan_steps"]],
    "rollback_command_preview": [step["command_preview"] for step in host_plan["rollback_plan_steps"]],
    "manual_next_step": "data-operations-live-scheduler-host-activation-execution-decision",
}
execution_request_path.write_text(json.dumps(execution_request, indent=2, sort_keys=True) + "\n", encoding="utf-8")

base_decision = {
    "report_name": "data_operations_live_scheduler_host_activation_execution_decision",
    "execution_request": "pending_explicit_execution_approval",
    "execution_request_report_path": str(execution_request_path),
    "scheduler_activation": "not_installed",
    "host_install_path_written": False,
    "launchctl_executed": False,
    "child_command_executed": False,
    "host_activation_execution_allowed_in_this_task": False,
    "job_id": "macro-weekly",
    "pipeline_name": "Macro Weekly",
    "domain": "macro",
    "cadence": "weekly",
}
approve_decision_path.write_text(
    json.dumps(
        {
            **base_decision,
            "decision_gate": "approved_for_host_activation_execution_final_preflight",
            "user_decision": "approve_host_activation_execution",
            "host_activation_execution_allowed_for_next_task": True,
            "manual_next_step": "data-operations-live-scheduler-host-activation-execution-final-preflight",
        },
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)
deny_decision_path.write_text(
    json.dumps(
        {
            **base_decision,
            "decision_gate": "denied_host_activation_execution",
            "user_decision": "deny_host_activation_execution",
            "host_activation_execution_allowed_for_next_task": False,
            "manual_next_step": "data-operations-live-scheduler-host-activation-execution-request",
        },
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)

drift_plan = {**host_plan, "execution_plan_steps": [{**host_plan["execution_plan_steps"][0], "command_preview": "launchctl bootstrap drifted.plist"}]}
drift_host_plan_path.write_text(json.dumps(drift_plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
drift_request = {**execution_request, "host_activation_plan_report_path": str(drift_host_plan_path)}
drift_request_path.write_text(json.dumps(drift_request, indent=2, sort_keys=True) + "\n", encoding="utf-8")
drift_decision = {
    **base_decision,
    "execution_request_report_path": str(drift_request_path),
    "decision_gate": "approved_for_host_activation_execution_final_preflight",
    "user_decision": "approve_host_activation_execution",
    "host_activation_execution_allowed_for_next_task": True,
    "manual_next_step": "data-operations-live-scheduler-host-activation-execution-final-preflight",
}
drift_decision_path.write_text(json.dumps(drift_decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

APPROVE_FINAL_PREFLIGHT_REPORT=$(scripts/preflight_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-decision-report "$APPROVE_EXECUTION_DECISION_REPORT" \
  --env-file "$ENV_FILE" \
  --output-dir "$APPROVE_OUTPUT_DIR")

DENY_FINAL_PREFLIGHT_REPORT=$(scripts/preflight_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-decision-report "$DENY_EXECUTION_DECISION_REPORT" \
  --env-file "$ENV_FILE" \
  --output-dir "$DENY_OUTPUT_DIR")

BAD_ENV_FINAL_PREFLIGHT_REPORT=$(scripts/preflight_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-decision-report "$APPROVE_EXECUTION_DECISION_REPORT" \
  --env-file "$BAD_ENV_FILE" \
  --output-dir "$BAD_ENV_OUTPUT_DIR")

"$PYTHON_BIN" - "$APPROVE_FINAL_PREFLIGHT_REPORT" "$DENY_FINAL_PREFLIGHT_REPORT" "$BAD_ENV_FINAL_PREFLIGHT_REPORT" "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

approve = json.load(open(sys.argv[1], encoding="utf-8"))
deny = json.load(open(sys.argv[2], encoding="utf-8"))
bad_env = json.load(open(sys.argv[3], encoding="utf-8"))
repo_root = Path(sys.argv[4]).resolve()

assert approve["report_name"] == "data_operations_live_scheduler_host_activation_execution_final_preflight"
assert approve["execution_final_preflight"] == "passed_ready_for_host_activation_execution_task"
assert approve["host_activation_execution_allowed_for_next_task"] is True
assert approve["host_activation_execution_allowed_in_this_task"] is False
assert approve["launchctl_executed"] is False
assert approve["host_install_path_written"] is False
assert approve["child_command_executed"] is False
assert approve["manual_next_step"] == "data-operations-live-scheduler-host-activation-execution"
assert not Path(approve["execution_decision_report_path"]).resolve().is_relative_to(repo_root)
assert not Path(approve["runtime_env_readiness_report_path"]).resolve().is_relative_to(repo_root)

assert deny["execution_final_preflight"] == "blocked_execution_decision_not_approved"
assert deny["host_activation_execution_allowed_for_next_task"] is False
assert deny["manual_next_step"] == "data-operations-live-scheduler-host-activation-execution-decision"

assert bad_env["execution_final_preflight"] == "blocked_runtime_env_not_ready"
assert bad_env["host_activation_execution_allowed_for_next_task"] is False
assert bad_env["manual_next_step"] == "data-operations-live-scheduler-host-activation-execution-final-preflight"
assert bad_env["runtime_env_issues"]

text = json.dumps([approve, deny, bad_env])
for forbidden in [
    "postgresql://execution_final_user:execution_final_pass",
    "fred-execution-final-token-123",
    "alpha-execution-final-token-123",
    "openai-execution-final-key-123456",
    "operator@test.invalid",
]:
    assert forbidden not in text, forbidden
PY

if scripts/preflight_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-decision-report "$DRIFT_DECISION_REPORT" \
  --env-file "$ENV_FILE" \
  --output-dir "$TMP_DIR/drift-output" >/tmp/stockanalysis-execution-final-drift.out 2>&1; then
  echo "Host activation execution final preflight must reject command preview drift." >&2
  exit 1
fi
grep -q "command preview must match" /tmp/stockanalysis-execution-final-drift.out

if scripts/preflight_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-decision-report "$ROOT_DIR/README.md" \
  --env-file "$ENV_FILE" \
  --output-dir "$TMP_DIR/readme-output" >/tmp/stockanalysis-execution-final-decision.out 2>&1; then
  echo "Host activation execution final preflight must refuse repo-inside execution decision reports." >&2
  exit 1
fi
grep -q "outside repository" /tmp/stockanalysis-execution-final-decision.out

if scripts/preflight_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-decision-report "$APPROVE_EXECUTION_DECISION_REPORT" \
  --env-file "$ROOT_DIR/README.md" \
  --output-dir "$TMP_DIR/readme-env-output" >/tmp/stockanalysis-execution-final-env.out 2>&1; then
  echo "Host activation execution final preflight must refuse repo-inside env files." >&2
  exit 1
fi
grep -q "outside repository" /tmp/stockanalysis-execution-final-env.out

if scripts/preflight_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-decision-report "$APPROVE_EXECUTION_DECISION_REPORT" \
  --env-file "$ENV_FILE" \
  --host-activation-plan-report "$ROOT_DIR/README.md" \
  --output-dir "$TMP_DIR/readme-plan-output" >/tmp/stockanalysis-execution-final-plan.out 2>&1; then
  echo "Host activation execution final preflight must refuse repo-inside host activation plan reports." >&2
  exit 1
fi
grep -q "outside repository" /tmp/stockanalysis-execution-final-plan.out

if scripts/preflight_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-decision-report "$APPROVE_EXECUTION_DECISION_REPORT" \
  --env-file "$ENV_FILE" \
  --output-dir "$ROOT_DIR/tmp-execution-final-preflight" >/tmp/stockanalysis-execution-final-output.out 2>&1; then
  echo "Host activation execution final preflight must refuse repo-inside output dirs." >&2
  exit 1
fi
grep -q "outside repository" /tmp/stockanalysis-execution-final-output.out

test -f docs/data-operations-live-scheduler-host-activation-execution-final-preflight.md
test -f docs/plans/2026-05-11-data-operations-live-scheduler-host-activation-execution-final-preflight.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution-final-preflight/contract.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution-final-preflight/plan.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution-final-preflight/handoff.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution-final-preflight/review.md

grep -q "preflight_data_operations_live_scheduler_host_activation_execution.sh" docs/data-operations-live-scheduler-host-activation-execution-final-preflight.md
grep -q "passed_ready_for_host_activation_execution_task" docs/data-operations-live-scheduler-host-activation-execution-final-preflight.md
grep -q "blocked_runtime_env_not_ready" docs/data-operations-live-scheduler-host-activation-execution-final-preflight.md
grep -q "data-operations-live-scheduler-host-activation-execution-final-preflight" docs/project-execution-roadmap.md
grep -q 'Current task: `manual-host-scheduler-activation-explicit-approval`' docs/project-execution-roadmap.md
grep -q '현재 고정된 immediate next task는 `manual-host-scheduler-activation-explicit-approval`' AGENTS.md
grep -q "verify_data_operations_live_scheduler_host_activation_execution_final_preflight.sh" docs/verification-plan.md
grep -q "docs/data-operations-live-scheduler-host-activation-execution-final-preflight.md" README.md

PYTHONPATH=/Users/woody/ai/agent-work-harness/src "$PYTHON_BIN" -m awh verify --repo "$ROOT_DIR" --task data-operations-live-scheduler-host-activation-execution-final-preflight

echo "data operations live scheduler host activation execution final preflight verification passed"
