#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/stockanalysis-data-ops-approval-gate.XXXXXX")
trap 'rm -rf "$TMP_DIR"' EXIT

cd "$ROOT_DIR"

bash -n scripts/check_data_operations_scheduler_activation_approval_gate.sh
bash -n scripts/verify_data_operations_scheduler_activation_approval_gate.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/operations/scheduler_activation_approval.py \
  src/stockanalysis/operations/scheduler_operator_dry_run.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_data_operations_scheduler_activation_approval \
  tests.test_data_operations_scheduler_operator_dry_run \
  -v

if grep -Eq '^[[:space:]]*launchctl[[:space:]]' scripts/check_data_operations_scheduler_activation_approval_gate.sh; then
  echo "Approval gate script must not execute launchctl." >&2
  exit 1
fi

ENV_FILE="$TMP_DIR/data-operations.env"
POSITIONS_CSV="$TMP_DIR/positions.csv"
MARKET_WATCHLIST_CSV="$TMP_DIR/market-watchlist.csv"
ARTIFACT_ROOT="$TMP_DIR/artifacts"
DRY_RUN_OUTPUT_DIR="$TMP_DIR/operator-dry-run"
PENDING_GATE_REPORT="$TMP_DIR/pending-approval-gate.json"
APPROVAL_RECORD="$TMP_DIR/activation-approval.json"
APPROVED_GATE_REPORT="$TMP_DIR/approved-approval-gate.json"

cat > "$POSITIONS_CSV" <<'CSV'
symbol,quantity
AAPL,10
CSV

cat > "$MARKET_WATCHLIST_CSV" <<'CSV'
symbol
AAPL
MSFT
CSV

cat > "$ENV_FILE" <<ENV
STOCKANALYSIS_DATABASE_URL="postgresql://approval_user:approval_pass@db.internal:5432/stockanalysis"
STOCKANALYSIS_FRED_API_KEY="fred-approval-token-123"
STOCKANALYSIS_MARKET_PRICE_PROVIDER="twelve_data"
STOCKANALYSIS_TWELVE_DATA_API_KEY="twelve-approval-token-123"
STOCKANALYSIS_MARKET_PRICE_WATCHLIST_CSV="$MARKET_WATCHLIST_CSV"
STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH="$TMP_DIR/market-ledger.json"
STOCKANALYSIS_ALPHA_VANTAGE_API_KEY="alpha-approval-token-123"
STOCKANALYSIS_SEC_USER_AGENT="stockanalysis-approval-gate operator@test.invalid"
STOCKANALYSIS_PORTFOLIO_POSITIONS_CSV="$POSITIONS_CSV"
STOCKANALYSIS_LLM_PROVIDER="openai"
OPENAI_API_KEY="openai-approval-key-123456"
STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="$ARTIFACT_ROOT"
ENV
chmod 600 "$ENV_FILE"

OPERATOR_DRY_RUN_REPORT=$(scripts/dry_run_data_operations_scheduler_operator_flow.sh \
  --env-file "$ENV_FILE" \
  --job-id market-price-daily \
  --output-dir "$DRY_RUN_OUTPUT_DIR" \
  --run-date 2026-05-15 \
  --timeout-seconds 600 \
  -- "$PYTHON_BIN" -m stockanalysis.operations.cli market-price-daily-run \
    --skip-if-fresh)

scripts/check_data_operations_scheduler_activation_approval_gate.sh \
  --operator-dry-run-report "$OPERATOR_DRY_RUN_REPORT" \
  --output "$PENDING_GATE_REPORT" >/dev/null

"$PYTHON_BIN" - "$PENDING_GATE_REPORT" <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
assert payload["report_name"] == "data_operations_scheduler_activation_approval_gate"
assert payload["approval_gate"] == "blocked_pending_manual_approval"
assert payload["activation_allowed"] is False
assert payload["launchctl_executed"] is False
assert payload["host_install_path_written"] is False
assert payload["job_id"] == "market-price-daily"
PY

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
    "job_id": "market-price-daily",
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

"$PYTHON_BIN" - "$APPROVED_GATE_REPORT" "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

payload = json.load(open(sys.argv[1], encoding="utf-8"))
repo_root = Path(sys.argv[2]).resolve()
assert payload["approval_gate"] == "approved_for_manual_activation"
assert payload["activation_allowed"] is True
assert payload["approval_decision"] == "approved"
assert payload["launchctl_executed"] is False
assert payload["host_install_path_written"] is False
assert payload["child_command_executed"] is False
assert payload["manual_next_step"] == "data-operations-live-scheduler-activation-request"
assert not Path(payload["approval_record_path"]).resolve().is_relative_to(repo_root)
assert not Path(payload["operator_dry_run_report_path"]).resolve().is_relative_to(repo_root)
text = json.dumps(payload)
for forbidden in [
    "postgresql://approval_user:approval_pass",
    "fred-approval-token-123",
    "twelve-approval-token-123",
    "alpha-approval-token-123",
    "openai-approval-key-123456",
    "operator@test.invalid",
]:
    assert forbidden not in text, forbidden
PY

if scripts/check_data_operations_scheduler_activation_approval_gate.sh \
  --operator-dry-run-report "$ROOT_DIR/README.md" >/tmp/stockanalysis-approval-gate-readme.out 2>&1; then
  echo "Approval gate must refuse repo-inside operator dry-run reports." >&2
  exit 1
fi
grep -q "inside repository" /tmp/stockanalysis-approval-gate-readme.out

if scripts/check_data_operations_scheduler_activation_approval_gate.sh \
  --operator-dry-run-report "$OPERATOR_DRY_RUN_REPORT" \
  --approval-record "$ROOT_DIR/README.md" >/tmp/stockanalysis-approval-gate-approval.out 2>&1; then
  echo "Approval gate must refuse repo-inside approval records." >&2
  exit 1
fi
grep -q "inside repository" /tmp/stockanalysis-approval-gate-approval.out

test -f docs/data-operations-scheduler-activation-approval-gate.md
test -f docs/plans/2026-05-11-data-operations-scheduler-activation-approval-gate.md
test -f docs/tasks/data-operations-scheduler-activation-approval-gate/contract.md
test -f docs/tasks/data-operations-scheduler-activation-approval-gate/plan.md
test -f docs/tasks/data-operations-scheduler-activation-approval-gate/handoff.md
test -f docs/tasks/data-operations-scheduler-activation-approval-gate/review.md

grep -q "check_data_operations_scheduler_activation_approval_gate.sh" docs/data-operations-scheduler-activation-approval-gate.md
grep -q "blocked_pending_manual_approval" docs/data-operations-scheduler-activation-approval-gate.md
grep -q "approved_for_manual_activation" docs/data-operations-scheduler-activation-approval-gate.md
grep -q "data-operations-scheduler-activation-approval-gate" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-request" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-user-decision" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-final-preflight" docs/project-execution-roadmap.md
grep -q 'Current task: `local-live-mvp-runtime`' docs/project-execution-roadmap.md
grep -q '현재 고정된 immediate next task는 `local-live-mvp-runtime`' AGENTS.md
grep -q "verify_data_operations_scheduler_activation_approval_gate.sh" docs/verification-plan.md
grep -q "docs/data-operations-scheduler-activation-approval-gate.md" README.md

PYTHONPATH=/Users/woody/ai/agent-work-harness/src "$PYTHON_BIN" -m awh verify --repo "$ROOT_DIR" --task data-operations-scheduler-activation-approval-gate

echo "data operations scheduler activation approval gate verification passed"
