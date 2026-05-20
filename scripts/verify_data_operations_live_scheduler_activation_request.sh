#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/stockanalysis-data-ops-activation-request.XXXXXX")
trap 'rm -rf "$TMP_DIR"' EXIT

cd "$ROOT_DIR"

bash -n scripts/request_data_operations_live_scheduler_activation.sh
bash -n scripts/verify_data_operations_live_scheduler_activation_request.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/operations/scheduler_activation_request.py \
  src/stockanalysis/operations/scheduler_activation_approval.py \
  src/stockanalysis/operations/scheduler_operator_dry_run.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_data_operations_scheduler_activation_request \
  tests.test_data_operations_scheduler_activation_approval \
  tests.test_data_operations_scheduler_operator_dry_run \
  -v

if grep -Eq '^[[:space:]]*launchctl[[:space:]]' scripts/request_data_operations_live_scheduler_activation.sh; then
  echo "Activation request script must not execute launchctl." >&2
  exit 1
fi

ENV_FILE="$TMP_DIR/data-operations.env"
POSITIONS_CSV="$TMP_DIR/positions.csv"
ARTIFACT_ROOT="$TMP_DIR/artifacts"
DRY_RUN_OUTPUT_DIR="$TMP_DIR/operator-dry-run"
PENDING_GATE_REPORT="$TMP_DIR/pending-approval-gate.json"
APPROVAL_RECORD="$TMP_DIR/activation-approval.json"
APPROVED_GATE_REPORT="$TMP_DIR/approved-approval-gate.json"
REQUEST_REPORT="$TMP_DIR/live-activation-request.json"
DERIVED_REQUEST_REPORT="$TMP_DIR/live-activation-request-derived.json"

cat > "$POSITIONS_CSV" <<'CSV'
symbol,quantity
AAPL,10
CSV

cat > "$ENV_FILE" <<ENV
STOCKANALYSIS_DATABASE_URL="postgresql://request_user:request_pass@db.internal:5432/stockanalysis"
STOCKANALYSIS_FRED_API_KEY="fred-request-token-123"
STOCKANALYSIS_ALPHA_VANTAGE_API_KEY="alpha-request-token-123"
STOCKANALYSIS_SEC_USER_AGENT="stockanalysis-activation-request operator@test.invalid"
STOCKANALYSIS_PORTFOLIO_POSITIONS_CSV="$POSITIONS_CSV"
STOCKANALYSIS_LLM_PROVIDER="openai"
OPENAI_API_KEY="openai-request-key-123456"
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

scripts/check_data_operations_scheduler_activation_approval_gate.sh \
  --operator-dry-run-report "$OPERATOR_DRY_RUN_REPORT" \
  --output "$PENDING_GATE_REPORT" >/dev/null

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

"$PYTHON_BIN" - "$REQUEST_REPORT" "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

payload = json.load(open(sys.argv[1], encoding="utf-8"))
repo_root = Path(sys.argv[2]).resolve()
assert payload["report_name"] == "data_operations_live_scheduler_activation_request"
assert payload["activation_request"] == "pending_explicit_user_approval"
assert payload["requires_explicit_user_approval"] is True
assert payload["activation_allowed_by_gate"] is True
assert payload["scheduler_activation"] == "not_installed"
assert payload["launchctl_executed"] is False
assert payload["host_install_path_written"] is False
assert payload["child_command_executed"] is False
assert payload["manual_next_step"] == "data-operations-live-scheduler-activation-user-decision"
assert "approve_live_scheduler_activation" in payload["requested_user_decision_values"]
assert "deny_live_scheduler_activation" in payload["requested_user_decision_values"]
assert "launchctl bootstrap" in "\n".join(payload["activation_command_preview"])
assert "launchctl bootout" in "\n".join(payload["rollback_command_preview"])
assert payload["host_plist_path_preview"].startswith("$HOME/Library/LaunchAgents/")
command_text = "\n".join(payload["activation_command_preview"] + payload["rollback_command_preview"])
assert '"$HOME/Library/LaunchAgents/' in command_text
assert '"~/Library/LaunchAgents' not in command_text
assert not Path(payload["approval_gate_report_path"]).resolve().is_relative_to(repo_root)
assert not Path(payload["operator_dry_run_report_path"]).resolve().is_relative_to(repo_root)
text = json.dumps(payload)
for forbidden in [
    "postgresql://request_user:request_pass",
    "fred-request-token-123",
    "alpha-request-token-123",
    "openai-request-key-123456",
    "operator@test.invalid",
]:
    assert forbidden not in text, forbidden
PY

scripts/request_data_operations_live_scheduler_activation.sh \
  --approval-gate-report "$APPROVED_GATE_REPORT" \
  --output "$DERIVED_REQUEST_REPORT" >/dev/null

"$PYTHON_BIN" - "$DERIVED_REQUEST_REPORT" <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
assert payload["operator_dry_run_report_path"]
assert payload["activation_request"] == "pending_explicit_user_approval"
PY

if scripts/request_data_operations_live_scheduler_activation.sh \
  --approval-gate-report "$PENDING_GATE_REPORT" \
  --operator-dry-run-report "$OPERATOR_DRY_RUN_REPORT" >/tmp/stockanalysis-activation-request-pending.out 2>&1; then
  echo "Activation request must reject pending approval gates." >&2
  exit 1
fi
grep -q "approved_for_manual_activation" /tmp/stockanalysis-activation-request-pending.out

if scripts/request_data_operations_live_scheduler_activation.sh \
  --approval-gate-report "$ROOT_DIR/README.md" >/tmp/stockanalysis-activation-request-readme.out 2>&1; then
  echo "Activation request must refuse repo-inside approval gate reports." >&2
  exit 1
fi
grep -q "inside repository" /tmp/stockanalysis-activation-request-readme.out

if scripts/request_data_operations_live_scheduler_activation.sh \
  --approval-gate-report "$APPROVED_GATE_REPORT" \
  --operator-dry-run-report "$ROOT_DIR/README.md" >/tmp/stockanalysis-activation-request-operator.out 2>&1; then
  echo "Activation request must refuse repo-inside operator dry-run reports." >&2
  exit 1
fi
grep -q "inside repository" /tmp/stockanalysis-activation-request-operator.out

test -f docs/data-operations-live-scheduler-activation-request.md
test -f docs/plans/2026-05-11-data-operations-live-scheduler-activation-request.md
test -f docs/tasks/data-operations-live-scheduler-activation-request/contract.md
test -f docs/tasks/data-operations-live-scheduler-activation-request/plan.md
test -f docs/tasks/data-operations-live-scheduler-activation-request/handoff.md
test -f docs/tasks/data-operations-live-scheduler-activation-request/review.md

grep -q "request_data_operations_live_scheduler_activation.sh" docs/data-operations-live-scheduler-activation-request.md
grep -q "pending_explicit_user_approval" docs/data-operations-live-scheduler-activation-request.md
grep -q "data-operations-live-scheduler-activation-user-decision" docs/data-operations-live-scheduler-activation-request.md
grep -q "data-operations-live-scheduler-activation-request" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-user-decision" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-final-preflight" docs/project-execution-roadmap.md
grep -q 'Current task: `local-live-mvp-runtime`' docs/project-execution-roadmap.md
grep -q '현재 고정된 immediate next task는 `local-live-mvp-runtime`' AGENTS.md
grep -q "verify_data_operations_live_scheduler_activation_request.sh" docs/verification-plan.md
grep -q "docs/data-operations-live-scheduler-activation-request.md" README.md

PYTHONPATH=/Users/woody/ai/agent-work-harness/src "$PYTHON_BIN" -m awh verify --repo "$ROOT_DIR" --task data-operations-live-scheduler-activation-request

echo "data operations live scheduler activation request verification passed"
