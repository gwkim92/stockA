#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"
ARTIFACT_ROOT=$(mktemp -d /tmp/stockanalysis-data-ops-artifacts.XXXXXX)
SUMMARY_PATH=$(mktemp)
trap 'rm -rf "$ARTIFACT_ROOT"; rm -f "$SUMMARY_PATH"' EXIT

cd "$ROOT_DIR"

bash -n scripts/verify_data_operations_artifact_runner.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/operations/artifact_runner.py \
  src/stockanalysis/operations/cadence.py \
  src/stockanalysis/ingest/cli.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_data_operations_artifact_runner \
  tests.test_ingest_cli.IngestCliTests.test_data_operations_run_cli_captures_artifacts \
  tests.test_data_operations_cadence \
  -v

PYTHONPATH=src "$PYTHON_BIN" -m stockanalysis.ingest.cli \
  data-operations-run \
  --job-id macro-weekly \
  --artifact-root "$ARTIFACT_ROOT" \
  -- "$PYTHON_BIN" -c 'import json; print(json.dumps({"runner": "ok"}))' \
  > "$SUMMARY_PATH"

"$PYTHON_BIN" - "$SUMMARY_PATH" <<'PY'
import json
import sys
from pathlib import Path

summary = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
artifact_dir = Path(summary["artifact_dir"])
assert summary["report_name"] == "data_operations_artifact_run"
assert summary["job_id"] == "macro-weekly"
assert summary["status"] == "succeeded"
assert summary["exit_code"] == 0
assert (artifact_dir / "stdout.txt").exists()
assert (artifact_dir / "stdout.json").exists()
assert (artifact_dir / "stderr.log").exists()
assert (artifact_dir / "metadata.json").exists()
metadata = json.loads((artifact_dir / "metadata.json").read_text(encoding="utf-8"))
assert metadata["command_argv"]
assert "STOCKANALYSIS_DATABASE_URL" not in json.dumps(metadata)
PY

test -f docs/data-operations-artifact-runner.md
test -f docs/plans/2026-05-03-data-operations-artifact-runner.md
test -f docs/tasks/data-operations-artifact-runner/contract.md
test -f docs/tasks/data-operations-artifact-runner/plan.md
test -f docs/tasks/data-operations-artifact-runner/handoff.md
test -f docs/tasks/data-operations-artifact-runner/review.md

grep -q "data-operations-run" src/stockanalysis/ingest/cli.py
grep -q "run_data_operation_artifact_command" src/stockanalysis/operations/artifact_runner.py
grep -q "redact_command_argv" src/stockanalysis/operations/artifact_runner.py
grep -q "STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT" docs/data-operations-artifact-runner.md
grep -q "data-operations-artifact-runner" docs/project-execution-roadmap.md
grep -q "data-operations-runtime-env-readiness" docs/project-execution-roadmap.md
grep -q "data-operations-runtime-smoke" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-activation-boundary" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-install-dry-run" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-alert-boundary" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-activation-runbook" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-operator-dry-run" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-activation-approval-gate" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-request" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-user-decision" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-final-preflight" docs/project-execution-roadmap.md
grep -q 'Current task: `manual-host-scheduler-activation-explicit-approval`' docs/project-execution-roadmap.md
grep -q '현재 고정된 immediate next task는 `manual-host-scheduler-activation-explicit-approval`' AGENTS.md
grep -q "verify_data_operations_artifact_runner.sh" docs/verification-plan.md
grep -q "docs/data-operations-artifact-runner.md" README.md

echo "data operations artifact runner verification passed"
