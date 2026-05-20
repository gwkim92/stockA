#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/stockanalysis-data-ops-scheduler.XXXXXX")
trap 'rm -rf "$TMP_DIR"' EXIT

bash -n scripts/run_data_operations_scheduler_job.sh
bash -n scripts/verify_data_operations_scheduler_activation_boundary.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/operations/scheduler_boundary.py \
  src/stockanalysis/operations/env_readiness.py \
  src/stockanalysis/operations/artifact_runner.py \
  src/stockanalysis/operations/cadence.py \
  src/stockanalysis/ingest/cli.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_data_operations_scheduler_boundary \
  tests.test_data_operations_env_readiness \
  tests.test_data_operations_artifact_runner \
  -v

ENV_FILE="$TMP_DIR/data-operations.env"
POSITIONS_CSV="$TMP_DIR/positions.csv"
ARTIFACT_ROOT="$TMP_DIR/artifacts"
PREFLIGHT_JSON="$TMP_DIR/preflight.json"
RUN_JSON="$TMP_DIR/run.json"
SKIP_JSON="$TMP_DIR/skip.json"

cat > "$POSITIONS_CSV" <<'CSV'
symbol,quantity
AAPL,10
CSV

cat > "$ENV_FILE" <<ENV
STOCKANALYSIS_PSQL_COMMAND="$PYTHON_BIN"
STOCKANALYSIS_FRED_API_KEY="fred-runtime-token-123"
STOCKANALYSIS_ALPHA_VANTAGE_API_KEY="alpha-runtime-token-123"
STOCKANALYSIS_SEC_USER_AGENT="stockanalysis-test contact@operator.test"
STOCKANALYSIS_PORTFOLIO_POSITIONS_CSV="$POSITIONS_CSV"
STOCKANALYSIS_LLM_PROVIDER="openai"
OPENAI_API_KEY="openai-runtime-key-123456"
STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="$ARTIFACT_ROOT"
ENV
chmod 600 "$ENV_FILE"

if scripts/run_data_operations_scheduler_job.sh --env-file "$ENV_FILE" --job-id macro-weekly >/tmp/stockanalysis-data-ops-scheduler-missing-command.out 2>&1; then
  echo "Scheduler wrapper must refuse missing command." >&2
  exit 1
fi
grep -q "Missing command after --" /tmp/stockanalysis-data-ops-scheduler-missing-command.out

if scripts/run_data_operations_scheduler_job.sh --env-file "$ROOT_DIR/README.md" --job-id macro-weekly -- "$PYTHON_BIN" -c 'print("{}")' >/tmp/stockanalysis-data-ops-scheduler-readme.out 2>&1; then
  echo "Scheduler wrapper must refuse repo-inside env files." >&2
  exit 1
fi
grep -q "inside repository" /tmp/stockanalysis-data-ops-scheduler-readme.out

PYTHON_BIN="$PYTHON_BIN" scripts/run_data_operations_scheduler_job.sh \
  --env-file "$ENV_FILE" \
  --job-id macro-weekly \
  --run-date 2026-05-04 \
  --skip-dates 2026-12-25 \
  --timeout-seconds 120 \
  --preflight-only \
  -- "$PYTHON_BIN" -c 'print("{}")' --api-key secret-value > "$PREFLIGHT_JSON"

"$PYTHON_BIN" - "$PREFLIGHT_JSON" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["report_name"] == "data_operations_scheduler_preflight"
assert payload["preflight"] == "passed"
assert payload["scheduler_activation"] == "boundary_only_not_installed"
assert payload["job_id"] == "macro-weekly"
assert payload["would_skip"] is False
assert "[REDACTED]" in payload["command_argv"]
text = json.dumps(payload)
for forbidden in [
    "secret-value",
    "fred-runtime-token-123",
    "alpha-runtime-token-123",
    "openai-runtime-key-123456",
    "contact@operator.test",
]:
    assert forbidden not in text, forbidden
PY

PYTHON_BIN="$PYTHON_BIN" scripts/run_data_operations_scheduler_job.sh \
  --env-file "$ENV_FILE" \
  --job-id macro-weekly \
  --run-date 2026-05-04 \
  --skip-dates "2026-05-04 2026-12-25" \
  --skip-reason market_holiday \
  -- "$PYTHON_BIN" -c 'raise SystemExit("child should not run")' > "$SKIP_JSON"

"$PYTHON_BIN" - "$SKIP_JSON" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["report_name"] == "data_operations_scheduler_skip"
assert payload["status"] == "skipped"
assert payload["job_id"] == "macro-weekly"
assert payload["skip_reason"] == "market_holiday"
artifact_dir = Path(payload["artifact_dir"])
assert (artifact_dir / "stdout.json").is_file()
assert (artifact_dir / "stderr.log").is_file()
assert (artifact_dir / "metadata.json").is_file()
assert "child should not run" not in (artifact_dir / "stderr.log").read_text(encoding="utf-8")
PY

PYTHON_BIN="$PYTHON_BIN" scripts/run_data_operations_scheduler_job.sh \
  --env-file "$ENV_FILE" \
  --job-id macro-weekly \
  --run-date 2026-05-05 \
  --timeout-seconds 120 \
  -- "$PYTHON_BIN" -c 'import json; print(json.dumps({"scheduler": "ok"}))' > "$RUN_JSON"

"$PYTHON_BIN" - "$RUN_JSON" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["report_name"] == "data_operations_artifact_run"
assert payload["job_id"] == "macro-weekly"
assert payload["status"] == "succeeded"
assert payload["stdout_format"] == "json"
artifact_dir = Path(payload["artifact_dir"])
assert (artifact_dir / "stdout.txt").is_file()
assert (artifact_dir / "stdout.json").is_file()
assert (artifact_dir / "stderr.log").is_file()
assert (artifact_dir / "metadata.json").is_file()
metadata = json.loads((artifact_dir / "metadata.json").read_text(encoding="utf-8"))
assert metadata["status"] == "succeeded"
assert "STOCKANALYSIS_FRED_API_KEY" not in json.dumps(metadata)
PY

for activation_path in \
  ".github/workflows/data-operations-scheduler.yml" \
  "cron/data-operations.cron" \
  "launchd/com.stockanalysis.data-operations.plist"
do
  if [ -e "$ROOT_DIR/$activation_path" ]; then
    echo "Unexpected scheduler activation artifact exists: $activation_path" >&2
    exit 1
  fi
done

test -f docs/data-operations-scheduler-activation-boundary.md
test -f docs/plans/2026-05-04-data-operations-scheduler-activation-boundary.md
test -f docs/tasks/data-operations-scheduler-activation-boundary/contract.md
test -f docs/tasks/data-operations-scheduler-activation-boundary/plan.md
test -f docs/tasks/data-operations-scheduler-activation-boundary/handoff.md
test -f docs/tasks/data-operations-scheduler-activation-boundary/review.md

grep -q "run_data_operations_scheduler_job.sh" docs/data-operations-scheduler-activation-boundary.md
grep -q "data-operations-scheduler-activation-boundary" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-install-dry-run" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-alert-boundary" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-activation-runbook" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-operator-dry-run" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-activation-approval-gate" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-request" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-user-decision" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-final-preflight" docs/project-execution-roadmap.md
grep -q "verify_data_operations_scheduler_activation_boundary.sh" docs/verification-plan.md
grep -q "docs/data-operations-scheduler-activation-boundary.md" README.md
grep -q 'Current task: `manual-host-scheduler-activation-explicit-approval`' docs/project-execution-roadmap.md
grep -q '현재 고정된 immediate next task는 `manual-host-scheduler-activation-explicit-approval`' AGENTS.md

PYTHONPATH=/Users/woody/ai/agent-work-harness/src "$PYTHON_BIN" -m awh verify --repo "$ROOT_DIR" --task data-operations-scheduler-activation-boundary

echo "data operations scheduler activation boundary verification passed"
