#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/stockanalysis-data-ops-operator-dry-run.XXXXXX")
trap 'rm -rf "$TMP_DIR"' EXIT

cd "$ROOT_DIR"

bash -n scripts/dry_run_data_operations_scheduler_operator_flow.sh
bash -n scripts/verify_data_operations_scheduler_operator_dry_run.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/operations/scheduler_operator_dry_run.py \
  src/stockanalysis/operations/scheduler_boundary.py \
  src/stockanalysis/operations/scheduler_install.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_data_operations_scheduler_operator_dry_run \
  tests.test_data_operations_scheduler_boundary \
  tests.test_data_operations_scheduler_install \
  -v

if grep -Eq '^[[:space:]]*launchctl[[:space:]]' scripts/dry_run_data_operations_scheduler_operator_flow.sh; then
  echo "Operator dry-run script must not execute launchctl." >&2
  exit 1
fi

ENV_FILE="$TMP_DIR/data-operations.env"
POSITIONS_CSV="$TMP_DIR/positions.csv"
MARKET_WATCHLIST_CSV="$TMP_DIR/market-watchlist.csv"
ARTIFACT_ROOT="$TMP_DIR/artifacts"
OUTPUT_DIR="$TMP_DIR/operator-dry-run"

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
STOCKANALYSIS_DATABASE_URL="postgresql://operator_user:operator_pass@db.internal:5432/stockanalysis"
STOCKANALYSIS_FRED_API_KEY="fred-operator-token-123"
STOCKANALYSIS_MARKET_PRICE_PROVIDER="twelve_data"
STOCKANALYSIS_TWELVE_DATA_API_KEY="twelve-operator-token-123"
STOCKANALYSIS_MARKET_PRICE_WATCHLIST_CSV="$MARKET_WATCHLIST_CSV"
STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH="$TMP_DIR/market-ledger.json"
STOCKANALYSIS_ALPHA_VANTAGE_API_KEY="alpha-operator-token-123"
STOCKANALYSIS_SEC_USER_AGENT="stockanalysis-operator-dry-run operator@test.invalid"
STOCKANALYSIS_PORTFOLIO_POSITIONS_CSV="$POSITIONS_CSV"
STOCKANALYSIS_LLM_PROVIDER="openai"
OPENAI_API_KEY="openai-operator-key-123456"
STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="$ARTIFACT_ROOT"
ENV
chmod 600 "$ENV_FILE"

REPORT_PATH=$(scripts/dry_run_data_operations_scheduler_operator_flow.sh \
  --env-file "$ENV_FILE" \
  --job-id market-price-daily \
  --output-dir "$OUTPUT_DIR" \
  --run-date 2026-05-15 \
  --timeout-seconds 600 \
  -- "$PYTHON_BIN" -m stockanalysis.operations.cli market-price-daily-run \
    --skip-if-fresh)

"$PYTHON_BIN" - "$REPORT_PATH" "$ROOT_DIR" "$OUTPUT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report_path = Path(sys.argv[1]).resolve()
repo_root = Path(sys.argv[2]).resolve()
output_dir = Path(sys.argv[3]).resolve()
payload = json.loads(report_path.read_text(encoding="utf-8"))

assert payload["report_name"] == "data_operations_scheduler_operator_dry_run"
assert payload["operator_dry_run"] == "passed"
assert payload["scheduler_activation"] == "not_installed"
assert payload["host_install_path_written"] is False
assert payload["launchctl_executed"] is False
assert payload["child_command_executed"] is False
assert payload["requires_manual_approval"] is True
assert payload["job_id"] == "market-price-daily"
assert payload["manual_next_step"] == "data-operations-scheduler-activation-approval-gate"
assert output_dir == Path(payload["output_dir"]).resolve()
assert not output_dir.is_relative_to(repo_root)

paths = payload["evidence_paths"]
for key in [
    "env_readiness_report",
    "scheduler_preflight_report",
    "install_manifest",
    "plist",
    "alert_validation_output",
]:
    path = Path(paths[key]).resolve()
    assert path.exists(), f"missing evidence path {key}: {path}"
    assert not path.is_relative_to(repo_root), f"evidence path must be outside repo: {path}"

text = json.dumps(payload)
for forbidden in [
    "postgresql://operator_user:operator_pass",
    "fred-operator-token-123",
    "twelve-operator-token-123",
    "alpha-operator-token-123",
    "openai-operator-key-123456",
    "operator@test.invalid",
]:
    assert forbidden not in text, forbidden
PY

if scripts/dry_run_data_operations_scheduler_operator_flow.sh \
  --env-file "$ROOT_DIR/README.md" \
  --job-id market-price-daily \
  --output-dir "$OUTPUT_DIR/reject-env" \
  -- "$PYTHON_BIN" -c 'print("{}")' >/tmp/stockanalysis-operator-dry-run-readme.out 2>&1; then
  echo "Operator dry-run must refuse repo-inside env files." >&2
  exit 1
fi
grep -q "inside repository" /tmp/stockanalysis-operator-dry-run-readme.out

if scripts/dry_run_data_operations_scheduler_operator_flow.sh \
  --env-file "$ENV_FILE" \
  --job-id market-price-daily \
  --output-dir "$ROOT_DIR/.operator-dry-run" \
  -- "$PYTHON_BIN" -c 'print("{}")' >/tmp/stockanalysis-operator-dry-run-output.out 2>&1; then
  echo "Operator dry-run must refuse repo-inside output dirs." >&2
  exit 1
fi
grep -q "inside repository" /tmp/stockanalysis-operator-dry-run-output.out

test -f docs/data-operations-scheduler-operator-dry-run.md
test -f docs/plans/2026-05-11-data-operations-scheduler-operator-dry-run.md
test -f docs/tasks/data-operations-scheduler-operator-dry-run/contract.md
test -f docs/tasks/data-operations-scheduler-operator-dry-run/plan.md
test -f docs/tasks/data-operations-scheduler-operator-dry-run/handoff.md
test -f docs/tasks/data-operations-scheduler-operator-dry-run/review.md

grep -q "dry_run_data_operations_scheduler_operator_flow.sh" docs/data-operations-scheduler-operator-dry-run.md
grep -q "operator-dry-run.json" docs/data-operations-scheduler-operator-dry-run.md
grep -q "launchctl" docs/data-operations-scheduler-operator-dry-run.md
grep -q "data-operations-scheduler-operator-dry-run" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-request" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-user-decision" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-final-preflight" docs/project-execution-roadmap.md
grep -q 'Current task: `local-live-mvp-runtime`' docs/project-execution-roadmap.md
grep -q '현재 고정된 immediate next task는 `local-live-mvp-runtime`' AGENTS.md
grep -q "verify_data_operations_scheduler_operator_dry_run.sh" docs/verification-plan.md
grep -q "docs/data-operations-scheduler-operator-dry-run.md" README.md

PYTHONPATH=/Users/woody/ai/agent-work-harness/src "$PYTHON_BIN" -m awh verify --repo "$ROOT_DIR" --task data-operations-scheduler-operator-dry-run

echo "data operations scheduler operator dry-run verification passed"
