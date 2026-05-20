#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/stockanalysis-manual-host-preflight.XXXXXX")
trap 'rm -rf "$TMP_DIR"' EXIT

cd "$ROOT_DIR"

bash -n scripts/preflight_manual_host_scheduler_activation.sh
bash -n scripts/verify_manual_host_scheduler_activation_preflight.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/operations/cli.py \
  src/stockanalysis/operations/env_file.py \
  src/stockanalysis/operations/env_readiness.py \
  src/stockanalysis/operations/manual_host_scheduler_activation_preflight.py \
  src/stockanalysis/operations/path_policy.py \
  src/stockanalysis/operations/report_io.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_manual_host_scheduler_activation_preflight \
  tests.test_data_operations_cli \
  -v

if grep -Eq '^[[:space:]]*launchctl[[:space:]]' scripts/preflight_manual_host_scheduler_activation.sh; then
  echo "Manual host scheduler activation preflight wrapper must not execute launchctl." >&2
  exit 1
fi
grep -q 'stockanalysis.operations.cli' scripts/preflight_manual_host_scheduler_activation.sh
grep -q 'manual-host-scheduler-activation-preflight' src/stockanalysis/operations/cli.py

APPROVAL_REPORT="$TMP_DIR/manual-approval.json"
BLOCKED_APPROVAL_REPORT="$TMP_DIR/blocked-manual-approval.json"
ENV_FILE="$TMP_DIR/data-operations.env"
BAD_ENV_FILE="$TMP_DIR/bad-data-operations.env"
OUTPUT_DIR="$TMP_DIR/preflight-output"
BLOCKED_OUTPUT_DIR="$TMP_DIR/blocked-preflight-output"
BAD_ENV_OUTPUT_DIR="$TMP_DIR/bad-env-preflight-output"
POSITIONS_CSV="$TMP_DIR/positions.csv"
ARTIFACT_ROOT="$TMP_DIR/artifacts"

printf 'symbol,quantity\nAAPL,1\n' > "$POSITIONS_CSV"
cat > "$ENV_FILE" <<EOF
STOCKANALYSIS_DATABASE_URL="postgresql://stockanalysis:stockanalysis@localhost:5432/stockanalysis"
STOCKANALYSIS_FRED_API_KEY="fred-key-12345"
STOCKANALYSIS_ALPHA_VANTAGE_API_KEY="alpha-key-12345"
STOCKANALYSIS_SEC_USER_AGENT="stockanalysis ops@stock.local"
STOCKANALYSIS_PORTFOLIO_POSITIONS_CSV="$POSITIONS_CSV"
STOCKANALYSIS_LLM_PROVIDER="openai"
OPENAI_API_KEY="openai-key-12345"
STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="$ARTIFACT_ROOT"
EOF
cat > "$BAD_ENV_FILE" <<EOF
STOCKANALYSIS_DATABASE_URL="postgresql://stockanalysis:stockanalysis@localhost:5432/stockanalysis"
STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="$ARTIFACT_ROOT"
EOF

"$PYTHON_BIN" - "$APPROVAL_REPORT" "$BLOCKED_APPROVAL_REPORT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

approval_path = Path(sys.argv[1])
blocked_path = Path(sys.argv[2])
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
base = {
    "report_name": "manual_host_scheduler_activation_explicit_approval",
    "host_activation_allowed_for_manual_operator": True,
    "scheduler_activation": "not_installed",
    "host_install_path_written": False,
    "launchctl_executed": False,
    "child_command_executed": False,
    "host_activation_execution_performed": False,
    "codex_host_mutation_allowed": False,
    "job_id": "macro-weekly",
    "pipeline_name": "Macro Weekly",
    "domain": "macro",
    "cadence": "weekly",
    "rendered_label": "com.stockanalysis.data-operations.macro-weekly",
    "host_plist_path_preview": "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist",
    "exact_execution_commands": execution_commands,
    "exact_rollback_commands": rollback_commands,
}
approval_path.write_text(
    json.dumps(
        {
            **base,
            "approval_gate": "approved_for_manual_operator_host_activation_not_executed_by_codex",
            "manual_next_step": "manual-host-scheduler-activation-operator-evidence",
        },
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)
blocked_path.write_text(
    json.dumps(
        {
            **base,
            "approval_gate": "blocked_pending_exact_host_command_approval",
            "host_activation_allowed_for_manual_operator": False,
            "manual_next_step": "manual-host-scheduler-activation-explicit-approval",
        },
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)
PY

scripts/preflight_manual_host_scheduler_activation.sh \
  --manual-approval-report "$APPROVAL_REPORT" \
  --env-file "$ENV_FILE" \
  --output-dir "$OUTPUT_DIR" >/dev/null

scripts/preflight_manual_host_scheduler_activation.sh \
  --manual-approval-report "$BLOCKED_APPROVAL_REPORT" \
  --env-file "$ENV_FILE" \
  --output-dir "$BLOCKED_OUTPUT_DIR" >/dev/null

scripts/preflight_manual_host_scheduler_activation.sh \
  --manual-approval-report "$APPROVAL_REPORT" \
  --env-file "$BAD_ENV_FILE" \
  --output-dir "$BAD_ENV_OUTPUT_DIR" >/dev/null

"$PYTHON_BIN" - "$OUTPUT_DIR" "$BLOCKED_OUTPUT_DIR" "$BAD_ENV_OUTPUT_DIR" "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

passed = json.load(open(Path(sys.argv[1]) / "manual-host-scheduler-activation-preflight.json", encoding="utf-8"))
blocked = json.load(open(Path(sys.argv[2]) / "manual-host-scheduler-activation-preflight.json", encoding="utf-8"))
bad_env = json.load(open(Path(sys.argv[3]) / "manual-host-scheduler-activation-preflight.json", encoding="utf-8"))
repo_root = Path(sys.argv[4]).resolve()

assert passed["manual_activation_preflight"] == "passed_ready_for_external_manual_host_scheduler_activation"
assert passed["manual_operator_may_execute_exact_commands"] is True
assert passed["codex_host_mutation_allowed"] is False
assert passed["launchctl_executed"] is False
assert passed["host_install_path_written"] is False
assert not Path(passed["manual_approval_report_path"]).resolve().is_relative_to(repo_root)
assert (Path(sys.argv[1]) / "evidence" / "runtime-env-readiness.json").is_file()

assert blocked["manual_activation_preflight"] == "blocked_manual_approval_not_ready"
assert blocked["manual_operator_may_execute_exact_commands"] is False
assert blocked["manual_next_step"] == "manual-host-scheduler-activation-explicit-approval"

assert bad_env["manual_activation_preflight"] == "blocked_runtime_env_not_ready"
assert bad_env["manual_operator_may_execute_exact_commands"] is False
assert bad_env["runtime_env_issues"]

text = json.dumps([passed, blocked, bad_env])
assert "postgresql://" not in text
PY

if scripts/preflight_manual_host_scheduler_activation.sh \
  --manual-approval-report "$ROOT_DIR/README.md" \
  --env-file "$ENV_FILE" \
  --output-dir "$TMP_DIR/repo-inside-report-output" >/tmp/stockanalysis-manual-host-preflight-report.out 2>&1; then
  echo "Manual host scheduler activation preflight must refuse repo-inside approval reports." >&2
  exit 1
fi
grep -q "outside repository" /tmp/stockanalysis-manual-host-preflight-report.out

if scripts/preflight_manual_host_scheduler_activation.sh \
  --manual-approval-report "$APPROVAL_REPORT" \
  --env-file "$ROOT_DIR/README.md" \
  --output-dir "$TMP_DIR/repo-inside-env-output" >/tmp/stockanalysis-manual-host-preflight-env.out 2>&1; then
  echo "Manual host scheduler activation preflight must refuse repo-inside env files." >&2
  exit 1
fi
grep -q "outside repository" /tmp/stockanalysis-manual-host-preflight-env.out

if scripts/preflight_manual_host_scheduler_activation.sh \
  --manual-approval-report "$APPROVAL_REPORT" \
  --env-file "$ENV_FILE" \
  --output-dir "$ROOT_DIR/tmp-manual-host-preflight" >/tmp/stockanalysis-manual-host-preflight-output.out 2>&1; then
  echo "Manual host scheduler activation preflight must refuse repo-inside output dirs." >&2
  exit 1
fi
grep -q "outside repository" /tmp/stockanalysis-manual-host-preflight-output.out

test -f docs/manual-host-scheduler-activation-preflight.md
test -f docs/plans/2026-05-15-manual-host-scheduler-activation-preflight.md
test -f docs/tasks/manual-host-scheduler-activation-preflight/contract.md
test -f docs/tasks/manual-host-scheduler-activation-preflight/plan.md
test -f docs/tasks/manual-host-scheduler-activation-preflight/handoff.md
test -f docs/tasks/manual-host-scheduler-activation-preflight/review.md

grep -q "preflight_manual_host_scheduler_activation.sh" docs/manual-host-scheduler-activation-preflight.md
grep -q "passed_ready_for_external_manual_host_scheduler_activation" docs/manual-host-scheduler-activation-preflight.md
grep -q "manual-host-scheduler-activation-preflight" docs/project-execution-roadmap.md
grep -q 'Current task: `local-live-mvp-runtime`' docs/project-execution-roadmap.md
grep -q '현재 고정된 immediate next task는 `local-live-mvp-runtime`' AGENTS.md
grep -q "verify_manual_host_scheduler_activation_preflight.sh" docs/verification-plan.md
grep -q "docs/manual-host-scheduler-activation-preflight.md" README.md

PYTHONPATH=/Users/woody/ai/agent-work-harness/src "$PYTHON_BIN" -m awh verify --repo "$ROOT_DIR" --task manual-host-scheduler-activation-preflight

echo "manual host scheduler activation preflight verification passed"
