#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/stockanalysis-data-ops-execution-decision.XXXXXX")
trap 'rm -rf "$TMP_DIR"' EXIT

cd "$ROOT_DIR"

bash -n scripts/decide_data_operations_live_scheduler_host_activation_execution.sh
bash -n scripts/verify_data_operations_live_scheduler_host_activation_execution_decision.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/operations/cli.py \
  src/stockanalysis/operations/path_policy.py \
  src/stockanalysis/operations/report_io.py \
  src/stockanalysis/operations/scheduler_activation_execution_decision.py \
  src/stockanalysis/operations/scheduler_activation_execution_request.py \
  src/stockanalysis/operations/scheduler_activation_host_plan.py \
  src/stockanalysis/operations/scheduler_activation_final_preflight.py \
  src/stockanalysis/operations/scheduler_activation_decision.py \
  src/stockanalysis/operations/scheduler_activation_request.py \
  src/stockanalysis/operations/scheduler_activation_approval.py \
  src/stockanalysis/operations/scheduler_operator_dry_run.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_data_operations_cli \
  tests.test_data_operations_scheduler_activation_execution_decision \
  tests.test_data_operations_scheduler_activation_execution_request \
  tests.test_data_operations_scheduler_activation_host_plan \
  tests.test_data_operations_scheduler_activation_final_preflight \
  tests.test_data_operations_scheduler_activation_decision \
  tests.test_data_operations_scheduler_activation_request \
  tests.test_data_operations_scheduler_activation_approval \
  tests.test_data_operations_scheduler_operator_dry_run \
  -v

if grep -Eq '^[[:space:]]*launchctl[[:space:]]' scripts/decide_data_operations_live_scheduler_host_activation_execution.sh; then
  echo "Host activation execution decision script must not execute launchctl." >&2
  exit 1
fi

grep -q 'stockanalysis.operations.cli' scripts/decide_data_operations_live_scheduler_host_activation_execution.sh
grep -q 'stockanalysis-operations' pyproject.toml

ENV_FILE="$TMP_DIR/data-operations.env"
POSITIONS_CSV="$TMP_DIR/positions.csv"
ARTIFACT_ROOT="$TMP_DIR/artifacts"
DRY_RUN_OUTPUT_DIR="$TMP_DIR/operator-dry-run"
APPROVAL_RECORD="$TMP_DIR/activation-approval.json"
APPROVED_GATE_REPORT="$TMP_DIR/approved-approval-gate.json"
REQUEST_REPORT="$TMP_DIR/live-activation-request.json"
APPROVE_DECISION_RECORD="$TMP_DIR/approve-decision.json"
APPROVE_DECISION_REPORT="$TMP_DIR/approve-decision-report.json"
APPROVE_PREFLIGHT_DIR="$TMP_DIR/approve-final-preflight"
HOST_PLAN_DIR="$TMP_DIR/host-plan"
EXECUTION_REQUEST_JSON="$TMP_DIR/host-activation-execution-request.json"
MISSING_EXECUTION_DECISION_REPORT="$TMP_DIR/missing-execution-decision-report.json"
APPROVE_EXECUTION_DECISION_RECORD="$TMP_DIR/approve-execution-decision.json"
DENY_EXECUTION_DECISION_RECORD="$TMP_DIR/deny-execution-decision.json"
BAD_EXECUTION_DECISION_RECORD="$TMP_DIR/bad-execution-decision.json"
SECRET_EXECUTION_DECISION_RECORD="$TMP_DIR/secret-execution-decision.json"
APPROVE_EXECUTION_DECISION_REPORT="$TMP_DIR/approve-execution-decision-report.json"
DENY_EXECUTION_DECISION_REPORT="$TMP_DIR/deny-execution-decision-report.json"

cat > "$POSITIONS_CSV" <<'CSV'
symbol,quantity
AAPL,10
CSV

cat > "$ENV_FILE" <<ENV
STOCKANALYSIS_DATABASE_URL="postgresql://decision_user:decision_pass@db.internal:5432/stockanalysis"
STOCKANALYSIS_FRED_API_KEY="fred-decision-token-123"
STOCKANALYSIS_ALPHA_VANTAGE_API_KEY="alpha-decision-token-123"
STOCKANALYSIS_SEC_USER_AGENT="stockanalysis-execution-decision operator@test.invalid"
STOCKANALYSIS_PORTFOLIO_POSITIONS_CSV="$POSITIONS_CSV"
STOCKANALYSIS_LLM_PROVIDER="openai"
OPENAI_API_KEY="openai-decision-key-123456"
STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="$ARTIFACT_ROOT"
ENV
chmod 600 "$ENV_FILE"

OPERATOR_DRY_RUN_REPORT=$(scripts/dry_run_data_operations_scheduler_operator_flow.sh \
  --env-file "$ENV_FILE" \
  --job-id macro-weekly \
  --output-dir "$DRY_RUN_OUTPUT_DIR" \
  --run-date 2026-05-11 \
  --timeout-seconds 120 \
  -- "$PYTHON_BIN" -m stockanalysis.ingest.cli macro-batch-upsert \
    --fixtures-dir tests/fixtures \
    --series-id CPIAUCSL \
    --series-id FEDFUNDS)

"$PYTHON_BIN" - "$APPROVAL_RECORD" "$OPERATOR_DRY_RUN_REPORT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

approval_path = Path(sys.argv[1])
operator_report_path = sys.argv[2]
payload = {
    "approval_record": "data_operations_scheduler_activation_approval",
    "approval_decision": "approved",
    "operator": "operator-handle",
    "approved_at": "2026-05-11T12:00:00Z",
    "job_id": "macro-weekly",
    "operator_dry_run_report": operator_report_path,
    "activation_window": "2026-05-11T12:00:00Z/2026-05-11T13:00:00Z",
    "rollback_owner": "operator-handle",
    "acknowledged_commands": [
        "install -m 600",
        "launchctl bootstrap",
        "launchctl kickstart",
        "launchctl print",
    ],
    "acknowledged_risks": [
        "host_scheduler_state_change",
        "recurring_data_operation_execution",
        "rollback_required_if_first_run_fails",
    ],
}
approval_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

scripts/check_data_operations_scheduler_activation_approval_gate.sh \
  --operator-dry-run-report "$OPERATOR_DRY_RUN_REPORT" \
  --approval-record "$APPROVAL_RECORD" \
  --output "$APPROVED_GATE_REPORT" >/dev/null

scripts/request_data_operations_live_scheduler_activation.sh \
  --approval-gate-report "$APPROVED_GATE_REPORT" \
  --operator-dry-run-report "$OPERATOR_DRY_RUN_REPORT" \
  --output "$REQUEST_REPORT" \
  --request-note "request explicit user decision for macro-weekly activation" >/dev/null

"$PYTHON_BIN" - "$APPROVE_DECISION_RECORD" "$REQUEST_REPORT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

approve_path = Path(sys.argv[1])
request_report_path = sys.argv[2]
payload = {
    "decision_record": "data_operations_live_scheduler_activation_user_decision",
    "decision": "approve_live_scheduler_activation",
    "decider": "operator-handle",
    "decided_at": "2026-05-11T12:30:00Z",
    "job_id": "macro-weekly",
    "activation_request_report": request_report_path,
    "decision_scope": "data_operations_scheduler_host_activation",
    "acknowledged_request_state": "pending_explicit_user_approval",
    "acknowledged_mutation_boundary": [
        "host_launchagents_write",
        "launchctl_bootstrap",
        "recurring_data_operation_execution",
        "rollback_required_if_activation_fails",
    ],
    "operator_note": "fixture user decision",
}
approve_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

scripts/decide_data_operations_live_scheduler_activation.sh \
  --activation-request-report "$REQUEST_REPORT" \
  --decision-record "$APPROVE_DECISION_RECORD" \
  --output "$APPROVE_DECISION_REPORT" >/dev/null

APPROVE_PREFLIGHT_REPORT=$(scripts/preflight_data_operations_live_scheduler_activation.sh \
  --activation-decision-report "$APPROVE_DECISION_REPORT" \
  --env-file "$ENV_FILE" \
  --output-dir "$APPROVE_PREFLIGHT_DIR")

HOST_PLAN_JSON=$(scripts/plan_data_operations_live_scheduler_host_activation.sh \
  --final-preflight-report "$APPROVE_PREFLIGHT_REPORT" \
  --output-dir "$HOST_PLAN_DIR")

scripts/request_data_operations_live_scheduler_host_activation_execution.sh \
  --host-activation-plan-report "$HOST_PLAN_JSON" \
  --output "$EXECUTION_REQUEST_JSON" \
  --request-note "operator reviewed host activation plan" >/dev/null

scripts/decide_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-request-report "$EXECUTION_REQUEST_JSON" \
  --output "$MISSING_EXECUTION_DECISION_REPORT" >/dev/null

"$PYTHON_BIN" - \
  "$APPROVE_EXECUTION_DECISION_RECORD" \
  "$DENY_EXECUTION_DECISION_RECORD" \
  "$BAD_EXECUTION_DECISION_RECORD" \
  "$SECRET_EXECUTION_DECISION_RECORD" \
  "$EXECUTION_REQUEST_JSON" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

approve_path = Path(sys.argv[1])
deny_path = Path(sys.argv[2])
bad_path = Path(sys.argv[3])
secret_path = Path(sys.argv[4])
execution_request_report_path = sys.argv[5]
base = {
    "decision_record": "data_operations_live_scheduler_host_activation_execution_decision",
    "decider": "operator-handle",
    "decided_at": "2026-05-11T13:00:00Z",
    "job_id": "macro-weekly",
    "execution_request_report": execution_request_report_path,
    "decision_scope": "data_operations_scheduler_host_activation_execution",
    "acknowledged_request_state": "pending_explicit_execution_approval",
    "acknowledged_mutation_boundary": [
        "host_launchagents_write",
        "launchctl_bootstrap",
        "launchctl_kickstart",
        "launchctl_print",
        "rollback_required_if_activation_fails",
        "recurring_data_operation_execution",
    ],
    "operator_note": "fixture execution decision",
}
approve_path.write_text(
    json.dumps({**base, "decision": "approve_host_activation_execution"}, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
deny_path.write_text(
    json.dumps({**base, "decision": "deny_host_activation_execution"}, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
bad_path.write_text(
    json.dumps(
        {**base, "decision": "approve_host_activation_execution", "execution_request_report": "/tmp/wrong-request.json"},
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)
secret_path.write_text(
    json.dumps(
        {**base, "decision": "approve_host_activation_execution", "operator_note": "postgresql://user:pass@host/db"},
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)
PY

scripts/decide_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-request-report "$EXECUTION_REQUEST_JSON" \
  --decision-record "$APPROVE_EXECUTION_DECISION_RECORD" \
  --output "$APPROVE_EXECUTION_DECISION_REPORT" >/dev/null

scripts/decide_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-request-report "$EXECUTION_REQUEST_JSON" \
  --decision-record "$DENY_EXECUTION_DECISION_RECORD" \
  --output "$DENY_EXECUTION_DECISION_REPORT" >/dev/null

"$PYTHON_BIN" - "$MISSING_EXECUTION_DECISION_REPORT" "$APPROVE_EXECUTION_DECISION_REPORT" "$DENY_EXECUTION_DECISION_REPORT" "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

missing = json.load(open(sys.argv[1], encoding="utf-8"))
approve = json.load(open(sys.argv[2], encoding="utf-8"))
deny = json.load(open(sys.argv[3], encoding="utf-8"))
repo_root = Path(sys.argv[4]).resolve()

assert missing["decision_gate"] == "blocked_pending_execution_decision"
assert missing["host_activation_execution_allowed_for_next_task"] is False
assert missing["manual_next_step"] == "data-operations-live-scheduler-host-activation-execution-decision"

assert approve["report_name"] == "data_operations_live_scheduler_host_activation_execution_decision"
assert approve["decision_gate"] == "approved_for_host_activation_execution_final_preflight"
assert approve["user_decision"] == "approve_host_activation_execution"
assert approve["host_activation_execution_allowed_for_next_task"] is True
assert approve["host_activation_execution_allowed_in_this_task"] is False
assert approve["launchctl_executed"] is False
assert approve["host_install_path_written"] is False
assert approve["child_command_executed"] is False
assert approve["manual_next_step"] == "data-operations-live-scheduler-host-activation-execution-final-preflight"
assert not Path(approve["execution_request_report_path"]).resolve().is_relative_to(repo_root)

assert deny["decision_gate"] == "denied_host_activation_execution"
assert deny["user_decision"] == "deny_host_activation_execution"
assert deny["host_activation_execution_allowed_for_next_task"] is False
assert deny["host_activation_execution_allowed_in_this_task"] is False
assert deny["manual_next_step"] == "data-operations-live-scheduler-host-activation-execution-request"

text = json.dumps([missing, approve, deny])
for forbidden in [
    "postgresql://decision_user:decision_pass",
    "fred-decision-token-123",
    "alpha-decision-token-123",
    "openai-decision-key-123456",
    "operator@test.invalid",
]:
    assert forbidden not in text, forbidden
PY

if scripts/decide_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-request-report "$EXECUTION_REQUEST_JSON" \
  --decision-record "$BAD_EXECUTION_DECISION_RECORD" \
  --output "$TMP_DIR/bad-execution-decision-report.json" >/tmp/stockanalysis-execution-decision-bad.out 2>&1; then
  echo "Host activation execution decision must reject mismatched execution request paths." >&2
  exit 1
fi
grep -q "same execution request report path" /tmp/stockanalysis-execution-decision-bad.out

if scripts/decide_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-request-report "$EXECUTION_REQUEST_JSON" \
  --decision-record "$SECRET_EXECUTION_DECISION_RECORD" \
  --output "$TMP_DIR/secret-execution-decision-report.json" >/tmp/stockanalysis-execution-decision-secret.out 2>&1; then
  echo "Host activation execution decision must reject secret-like decision records." >&2
  exit 1
fi
grep -q "secret-like" /tmp/stockanalysis-execution-decision-secret.out

if scripts/decide_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-request-report "$ROOT_DIR/README.md" \
  --output "$TMP_DIR/readme-execution-decision-report.json" >/tmp/stockanalysis-execution-decision-readme.out 2>&1; then
  echo "Host activation execution decision must refuse repo-inside execution request reports." >&2
  exit 1
fi
grep -q "outside repository" /tmp/stockanalysis-execution-decision-readme.out

if scripts/decide_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-request-report "$EXECUTION_REQUEST_JSON" \
  --decision-record "$ROOT_DIR/README.md" \
  --output "$TMP_DIR/readme-decision-record-report.json" >/tmp/stockanalysis-execution-decision-record.out 2>&1; then
  echo "Host activation execution decision must refuse repo-inside decision records." >&2
  exit 1
fi
grep -q "outside repository" /tmp/stockanalysis-execution-decision-record.out

if scripts/decide_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-request-report "$EXECUTION_REQUEST_JSON" \
  --output "$ROOT_DIR/tmp-execution-decision-report.json" >/tmp/stockanalysis-execution-decision-output.out 2>&1; then
  echo "Host activation execution decision must refuse repo-inside output paths." >&2
  exit 1
fi
grep -q "outside repository" /tmp/stockanalysis-execution-decision-output.out

test -f docs/data-operations-live-scheduler-host-activation-execution-decision.md
test -f docs/plans/2026-05-11-data-operations-live-scheduler-host-activation-execution-decision.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution-decision/contract.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution-decision/plan.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution-decision/handoff.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution-decision/review.md

grep -q "decide_data_operations_live_scheduler_host_activation_execution.sh" docs/data-operations-live-scheduler-host-activation-execution-decision.md
grep -q "approved_for_host_activation_execution_final_preflight" docs/data-operations-live-scheduler-host-activation-execution-decision.md
grep -q "data-operations-live-scheduler-host-activation-execution-final-preflight" docs/data-operations-live-scheduler-host-activation-execution-decision.md
grep -q "data-operations-live-scheduler-host-activation-execution-decision" docs/project-execution-roadmap.md
grep -q 'Current task: `manual-host-scheduler-activation-explicit-approval`' docs/project-execution-roadmap.md
grep -q '현재 고정된 immediate next task는 `manual-host-scheduler-activation-explicit-approval`' AGENTS.md
grep -q "verify_data_operations_live_scheduler_host_activation_execution_decision.sh" docs/verification-plan.md
grep -q "docs/data-operations-live-scheduler-host-activation-execution-decision.md" README.md

PYTHONPATH=/Users/woody/ai/agent-work-harness/src "$PYTHON_BIN" -m awh verify --repo "$ROOT_DIR" --task data-operations-live-scheduler-host-activation-execution-decision

echo "data operations live scheduler host activation execution decision verification passed"
