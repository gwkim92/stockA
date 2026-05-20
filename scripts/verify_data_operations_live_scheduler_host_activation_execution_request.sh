#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/stockanalysis-data-ops-execution-request.XXXXXX")
trap 'rm -rf "$TMP_DIR"' EXIT

cd "$ROOT_DIR"

bash -n scripts/request_data_operations_live_scheduler_host_activation_execution.sh
bash -n scripts/verify_data_operations_live_scheduler_host_activation_execution_request.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/operations/scheduler_activation_execution_request.py \
  src/stockanalysis/operations/scheduler_activation_host_plan.py \
  src/stockanalysis/operations/scheduler_activation_final_preflight.py \
  src/stockanalysis/operations/scheduler_activation_decision.py \
  src/stockanalysis/operations/scheduler_activation_request.py \
  src/stockanalysis/operations/scheduler_activation_approval.py \
  src/stockanalysis/operations/scheduler_operator_dry_run.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_data_operations_scheduler_activation_execution_request \
  tests.test_data_operations_scheduler_activation_host_plan \
  tests.test_data_operations_scheduler_activation_final_preflight \
  tests.test_data_operations_scheduler_activation_decision \
  tests.test_data_operations_scheduler_activation_request \
  tests.test_data_operations_scheduler_activation_approval \
  tests.test_data_operations_scheduler_operator_dry_run \
  -v

if grep -Eq '^[[:space:]]*launchctl[[:space:]]' scripts/request_data_operations_live_scheduler_host_activation_execution.sh; then
  echo "Host activation execution request script must not execute launchctl." >&2
  exit 1
fi

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
BAD_HOST_PLAN_JSON="$TMP_DIR/bad-host-activation-plan.json"

cat > "$POSITIONS_CSV" <<'CSV'
symbol,quantity
AAPL,10
CSV

cat > "$ENV_FILE" <<ENV
STOCKANALYSIS_DATABASE_URL="postgresql://execution_user:execution_pass@db.internal:5432/stockanalysis"
STOCKANALYSIS_FRED_API_KEY="fred-execution-token-123"
STOCKANALYSIS_ALPHA_VANTAGE_API_KEY="alpha-execution-token-123"
STOCKANALYSIS_SEC_USER_AGENT="stockanalysis-execution-request operator@test.invalid"
STOCKANALYSIS_PORTFOLIO_POSITIONS_CSV="$POSITIONS_CSV"
STOCKANALYSIS_LLM_PROVIDER="openai"
OPENAI_API_KEY="openai-execution-key-123456"
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

REQUEST_OUTPUT=$(scripts/request_data_operations_live_scheduler_host_activation_execution.sh \
  --host-activation-plan-report "$HOST_PLAN_JSON" \
  --output "$EXECUTION_REQUEST_JSON" \
  --request-note "operator reviewed host activation plan")
"$PYTHON_BIN" - "$REQUEST_OUTPUT" "$EXECUTION_REQUEST_JSON" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

assert Path(sys.argv[1]).resolve() == Path(sys.argv[2]).resolve()
PY

"$PYTHON_BIN" - "$EXECUTION_REQUEST_JSON" "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

payload = json.load(open(sys.argv[1], encoding="utf-8"))
repo_root = Path(sys.argv[2]).resolve()
assert payload["report_name"] == "data_operations_live_scheduler_host_activation_execution_request"
assert payload["execution_request"] == "pending_explicit_execution_approval"
assert payload["requires_explicit_execution_approval"] is True
assert payload["execution_allowed_by_plan"] is True
assert payload["host_activation_execution_allowed_in_this_task"] is False
assert payload["launchctl_executed"] is False
assert payload["host_install_path_written"] is False
assert payload["child_command_executed"] is False
assert payload["manual_next_step"] == "data-operations-live-scheduler-host-activation-execution-decision"
assert "approve_host_activation_execution" in payload["requested_user_decision_values"]
assert "deny_host_activation_execution" in payload["requested_user_decision_values"]
assert "launchctl bootstrap" in "\n".join(payload["execution_command_preview"])
assert "launchctl bootout" in "\n".join(payload["rollback_command_preview"])
assert not Path(payload["host_activation_plan_report_path"]).resolve().is_relative_to(repo_root)
text = json.dumps(payload)
for forbidden in [
    "postgresql://execution_user:execution_pass",
    "fred-execution-token-123",
    "alpha-execution-token-123",
    "openai-execution-key-123456",
    "operator@test.invalid",
]:
    assert forbidden not in text, forbidden
PY

"$PYTHON_BIN" - "$HOST_PLAN_JSON" "$BAD_HOST_PLAN_JSON" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

payload = json.load(open(sys.argv[1], encoding="utf-8"))
payload["host_activation_plan"] = "blocked"
payload["activation_allowed_for_execution_request"] = False
Path(sys.argv[2]).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

if scripts/request_data_operations_live_scheduler_host_activation_execution.sh \
  --host-activation-plan-report "$BAD_HOST_PLAN_JSON" \
  --output "$TMP_DIR/bad-execution-request.json" >/tmp/stockanalysis-execution-request-bad-plan.out 2>&1; then
  echo "Host activation execution request must reject non-ready host plans." >&2
  exit 1
fi
grep -q "ready_for_execution_request" /tmp/stockanalysis-execution-request-bad-plan.out

if scripts/request_data_operations_live_scheduler_host_activation_execution.sh \
  --host-activation-plan-report "$ROOT_DIR/README.md" \
  --output "$TMP_DIR/readme-execution-request.json" >/tmp/stockanalysis-execution-request-readme.out 2>&1; then
  echo "Host activation execution request must refuse repo-inside host plan reports." >&2
  exit 1
fi
grep -q "inside repository" /tmp/stockanalysis-execution-request-readme.out

if scripts/request_data_operations_live_scheduler_host_activation_execution.sh \
  --host-activation-plan-report "$HOST_PLAN_JSON" \
  --output "$ROOT_DIR/tmp-execution-request.json" >/tmp/stockanalysis-execution-request-output.out 2>&1; then
  echo "Host activation execution request must refuse repo-inside output paths." >&2
  exit 1
fi
grep -q "inside repository" /tmp/stockanalysis-execution-request-output.out

if scripts/request_data_operations_live_scheduler_host_activation_execution.sh \
  --host-activation-plan-report "$HOST_PLAN_JSON" \
  --output "$TMP_DIR/secret-note-execution-request.json" \
  --request-note "postgresql://user:pass@host/db" >/tmp/stockanalysis-execution-request-secret.out 2>&1; then
  echo "Host activation execution request must reject secret-like notes." >&2
  exit 1
fi
grep -q "secret-like" /tmp/stockanalysis-execution-request-secret.out

test -f docs/data-operations-live-scheduler-host-activation-execution-request.md
test -f docs/plans/2026-05-11-data-operations-live-scheduler-host-activation-execution-request.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution-request/contract.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution-request/plan.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution-request/handoff.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution-request/review.md

grep -q "request_data_operations_live_scheduler_host_activation_execution.sh" docs/data-operations-live-scheduler-host-activation-execution-request.md
grep -q "pending_explicit_execution_approval" docs/data-operations-live-scheduler-host-activation-execution-request.md
grep -q "data-operations-live-scheduler-host-activation-execution-final-preflight" docs/data-operations-live-scheduler-host-activation-execution-request.md
grep -q "data-operations-live-scheduler-host-activation-execution-request" docs/project-execution-roadmap.md
grep -q 'Current task: `manual-host-scheduler-activation-explicit-approval`' docs/project-execution-roadmap.md
grep -q '현재 고정된 immediate next task는 `manual-host-scheduler-activation-explicit-approval`' AGENTS.md
grep -q "verify_data_operations_live_scheduler_host_activation_execution_request.sh" docs/verification-plan.md
grep -q "docs/data-operations-live-scheduler-host-activation-execution-request.md" README.md

PYTHONPATH=/Users/woody/ai/agent-work-harness/src "$PYTHON_BIN" -m awh verify --repo "$ROOT_DIR" --task data-operations-live-scheduler-host-activation-execution-request

echo "data operations live scheduler host activation execution request verification passed"
