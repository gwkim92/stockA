#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/stockanalysis-data-ops-final-preflight.XXXXXX")
trap 'rm -rf "$TMP_DIR"' EXIT

cd "$ROOT_DIR"

bash -n scripts/preflight_data_operations_live_scheduler_activation.sh
bash -n scripts/verify_data_operations_live_scheduler_activation_final_preflight.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/operations/scheduler_activation_final_preflight.py \
  src/stockanalysis/operations/scheduler_activation_decision.py \
  src/stockanalysis/operations/scheduler_activation_request.py \
  src/stockanalysis/operations/scheduler_activation_approval.py \
  src/stockanalysis/operations/scheduler_operator_dry_run.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_data_operations_scheduler_activation_final_preflight \
  tests.test_data_operations_scheduler_activation_decision \
  tests.test_data_operations_scheduler_activation_request \
  tests.test_data_operations_scheduler_activation_approval \
  tests.test_data_operations_scheduler_operator_dry_run \
  -v

if grep -Eq '^[[:space:]]*launchctl[[:space:]]' scripts/preflight_data_operations_live_scheduler_activation.sh; then
  echo "Activation final-preflight script must not execute launchctl." >&2
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
DENY_DECISION_RECORD="$TMP_DIR/deny-decision.json"
DENY_DECISION_REPORT="$TMP_DIR/deny-decision-report.json"
APPROVE_PREFLIGHT_DIR="$TMP_DIR/approve-final-preflight"
DENY_PREFLIGHT_DIR="$TMP_DIR/deny-final-preflight"

cat > "$POSITIONS_CSV" <<'CSV'
symbol,quantity
AAPL,10
CSV

cat > "$ENV_FILE" <<ENV
STOCKANALYSIS_DATABASE_URL="postgresql://final_user:final_pass@db.internal:5432/stockanalysis"
STOCKANALYSIS_FRED_API_KEY="fred-final-token-123"
STOCKANALYSIS_ALPHA_VANTAGE_API_KEY="alpha-final-token-123"
STOCKANALYSIS_SEC_USER_AGENT="stockanalysis-final-preflight operator@test.invalid"
STOCKANALYSIS_PORTFOLIO_POSITIONS_CSV="$POSITIONS_CSV"
STOCKANALYSIS_LLM_PROVIDER="openai"
OPENAI_API_KEY="openai-final-key-123456"
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

"$PYTHON_BIN" - "$APPROVE_DECISION_RECORD" "$DENY_DECISION_RECORD" "$REQUEST_REPORT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

approve_path = Path(sys.argv[1])
deny_path = Path(sys.argv[2])
request_report_path = sys.argv[3]
base = {
    "decision_record": "data_operations_live_scheduler_activation_user_decision",
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
approve_path.write_text(
    json.dumps({**base, "decision": "approve_live_scheduler_activation"}, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
deny_path.write_text(
    json.dumps({**base, "decision": "deny_live_scheduler_activation"}, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY

scripts/decide_data_operations_live_scheduler_activation.sh \
  --activation-request-report "$REQUEST_REPORT" \
  --decision-record "$APPROVE_DECISION_RECORD" \
  --output "$APPROVE_DECISION_REPORT" >/dev/null

scripts/decide_data_operations_live_scheduler_activation.sh \
  --activation-request-report "$REQUEST_REPORT" \
  --decision-record "$DENY_DECISION_RECORD" \
  --output "$DENY_DECISION_REPORT" >/dev/null

APPROVE_PREFLIGHT_REPORT=$(scripts/preflight_data_operations_live_scheduler_activation.sh \
  --activation-decision-report "$APPROVE_DECISION_REPORT" \
  --env-file "$ENV_FILE" \
  --output-dir "$APPROVE_PREFLIGHT_DIR")

"$PYTHON_BIN" - "$APPROVE_PREFLIGHT_REPORT" "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

payload = json.load(open(sys.argv[1], encoding="utf-8"))
repo_root = Path(sys.argv[2]).resolve()
assert payload["report_name"] == "data_operations_live_scheduler_activation_final_preflight"
assert payload["final_preflight"] == "passed_ready_for_host_activation_plan"
assert payload["activation_allowed_for_host_activation_plan"] is True
assert payload["host_activation_execution_allowed_in_this_task"] is False
assert payload["launchctl_executed"] is False
assert payload["host_install_path_written"] is False
assert payload["manual_next_step"] == "data-operations-live-scheduler-host-activation-plan"
for field in [
    "activation_decision_report_path",
    "activation_request_report_path",
    "approval_gate_report_path",
    "operator_dry_run_report_path",
    "runtime_env_readiness_report_path",
]:
    assert not Path(payload[field]).resolve().is_relative_to(repo_root), field
text = json.dumps(payload)
for forbidden in [
    "postgresql://final_user:final_pass",
    "fred-final-token-123",
    "alpha-final-token-123",
    "openai-final-key-123456",
    "operator@test.invalid",
]:
    assert forbidden not in text, forbidden
PY

test -f "$APPROVE_PREFLIGHT_DIR/evidence/fresh-runtime-env-readiness.json"

DENY_PREFLIGHT_REPORT=$(scripts/preflight_data_operations_live_scheduler_activation.sh \
  --activation-decision-report "$DENY_DECISION_REPORT" \
  --env-file "$ENV_FILE" \
  --output-dir "$DENY_PREFLIGHT_DIR")

"$PYTHON_BIN" - "$DENY_PREFLIGHT_REPORT" <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
assert payload["final_preflight"] == "blocked_user_decision_not_approved"
assert payload["activation_allowed_for_host_activation_plan"] is False
assert payload["launchctl_executed"] is False
assert payload["manual_next_step"] == "data-operations-live-scheduler-activation-user-decision"
PY

if scripts/preflight_data_operations_live_scheduler_activation.sh \
  --activation-decision-report "$ROOT_DIR/README.md" \
  --env-file "$ENV_FILE" \
  --output-dir "$TMP_DIR/repo-refusal" >/tmp/stockanalysis-final-preflight-decision.out 2>&1; then
  echo "Final preflight must refuse repo-inside decision reports." >&2
  exit 1
fi
grep -q "inside repository" /tmp/stockanalysis-final-preflight-decision.out

if scripts/preflight_data_operations_live_scheduler_activation.sh \
  --activation-decision-report "$APPROVE_DECISION_REPORT" \
  --env-file "$ROOT_DIR/README.md" \
  --output-dir "$TMP_DIR/env-refusal" >/tmp/stockanalysis-final-preflight-env.out 2>&1; then
  echo "Final preflight must refuse repo-inside env files." >&2
  exit 1
fi
grep -q "inside repository" /tmp/stockanalysis-final-preflight-env.out

if scripts/preflight_data_operations_live_scheduler_activation.sh \
  --activation-decision-report "$APPROVE_DECISION_REPORT" \
  --env-file "$ENV_FILE" \
  --output-dir "$ROOT_DIR/tmp-final-preflight" >/tmp/stockanalysis-final-preflight-output.out 2>&1; then
  echo "Final preflight must refuse repo-inside output dirs." >&2
  exit 1
fi
grep -q "inside repository" /tmp/stockanalysis-final-preflight-output.out

test -f docs/data-operations-live-scheduler-activation-final-preflight.md
test -f docs/plans/2026-05-11-data-operations-live-scheduler-activation-final-preflight.md
test -f docs/tasks/data-operations-live-scheduler-activation-final-preflight/contract.md
test -f docs/tasks/data-operations-live-scheduler-activation-final-preflight/plan.md
test -f docs/tasks/data-operations-live-scheduler-activation-final-preflight/handoff.md
test -f docs/tasks/data-operations-live-scheduler-activation-final-preflight/review.md

grep -q "preflight_data_operations_live_scheduler_activation.sh" docs/data-operations-live-scheduler-activation-final-preflight.md
grep -q "passed_ready_for_host_activation_plan" docs/data-operations-live-scheduler-activation-final-preflight.md
grep -q "blocked_runtime_env_not_ready" docs/data-operations-live-scheduler-activation-final-preflight.md
grep -q "data-operations-live-scheduler-activation-final-preflight" docs/project-execution-roadmap.md
grep -q 'Current task: `manual-host-scheduler-activation-explicit-approval`' docs/project-execution-roadmap.md
grep -q '현재 고정된 immediate next task는 `manual-host-scheduler-activation-explicit-approval`' AGENTS.md
grep -q "verify_data_operations_live_scheduler_activation_final_preflight.sh" docs/verification-plan.md
grep -q "docs/data-operations-live-scheduler-activation-final-preflight.md" README.md

PYTHONPATH=/Users/woody/ai/agent-work-harness/src "$PYTHON_BIN" -m awh verify --repo "$ROOT_DIR" --task data-operations-live-scheduler-activation-final-preflight

echo "data operations live scheduler activation final preflight verification passed"
