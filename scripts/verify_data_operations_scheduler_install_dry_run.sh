#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/stockanalysis-data-ops-install.XXXXXX")
trap 'rm -rf "$TMP_DIR"' EXIT

bash -n scripts/render_data_operations_scheduler_install.sh
bash -n scripts/run_data_operations_scheduler_job.sh
bash -n scripts/verify_data_operations_scheduler_install_dry_run.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/operations/scheduler_install.py \
  src/stockanalysis/operations/scheduler_boundary.py \
  src/stockanalysis/operations/cadence.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_data_operations_scheduler_install \
  tests.test_data_operations_scheduler_boundary \
  -v

ENV_FILE="$TMP_DIR/data-operations.env"
OUTPUT_DIR="$TMP_DIR/rendered"
MANIFEST_PATH_FILE="$TMP_DIR/manifest-path.txt"
cat > "$ENV_FILE" <<'ENV'
# Renderer only checks that this trusted env file exists outside the repository.
# Runtime readiness is validated by run_data_operations_scheduler_job.sh.
ENV
chmod 600 "$ENV_FILE"

if scripts/render_data_operations_scheduler_install.sh \
  --output-dir "$ROOT_DIR/.tmp-data-ops-scheduler-install" \
  --env-file "$ENV_FILE" \
  --job-id macro-weekly \
  -- "$PYTHON_BIN" -c 'print("{}")' >/tmp/stockanalysis-data-ops-install-output.err 2>&1; then
  echo "Renderer must refuse repo-inside output dirs." >&2
  exit 1
fi
grep -q "inside repository" /tmp/stockanalysis-data-ops-install-output.err

if scripts/render_data_operations_scheduler_install.sh \
  --output-dir "$OUTPUT_DIR" \
  --env-file "$ROOT_DIR/README.md" \
  --job-id macro-weekly \
  -- "$PYTHON_BIN" -c 'print("{}")' >/tmp/stockanalysis-data-ops-install-env.err 2>&1; then
  echo "Renderer must refuse repo-inside env files." >&2
  exit 1
fi
grep -q "inside repository" /tmp/stockanalysis-data-ops-install-env.err

if scripts/render_data_operations_scheduler_install.sh \
  --output-dir "$OUTPUT_DIR" \
  --env-file "$ENV_FILE" \
  --job-id macro-weekly \
  -- "$PYTHON_BIN" -c 'print("{}")' --api-key secret-value >/tmp/stockanalysis-data-ops-install-secret.err 2>&1; then
  echo "Renderer must refuse sensitive command argv." >&2
  exit 1
fi
grep -q "sensitive values" /tmp/stockanalysis-data-ops-install-secret.err

if scripts/render_data_operations_scheduler_install.sh \
  --output-dir "$OUTPUT_DIR" \
  --env-file "$ENV_FILE" \
  --job-id performance-outcome-monthly \
  -- "$PYTHON_BIN" -c 'print("{}")' >/tmp/stockanalysis-data-ops-install-monthly.err 2>&1; then
  echo "Renderer must reject monthly first-business-day jobs." >&2
  exit 1
fi
grep -q "Monthly first-business-day" /tmp/stockanalysis-data-ops-install-monthly.err

scripts/render_data_operations_scheduler_install.sh \
  --output-dir "$OUTPUT_DIR" \
  --env-file "$ENV_FILE" \
  --job-id macro-weekly \
  --timeout-seconds 120 \
  -- "$PYTHON_BIN" -m stockanalysis.ingest.cli macro-batch-upsert \
    --fixtures-dir tests/fixtures \
    --series-id CPIAUCSL \
    --series-id FEDFUNDS > "$MANIFEST_PATH_FILE"

MANIFEST_PATH=$(cat "$MANIFEST_PATH_FILE")

"$PYTHON_BIN" - "$MANIFEST_PATH" "$ROOT_DIR" "$ENV_FILE" <<'PY'
from __future__ import annotations

import json
import plistlib
import sys
from pathlib import Path

manifest_path, root_dir, env_file = sys.argv[1:]
manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
plist_path = Path(manifest["plist_path"])

assert manifest["report_name"] == "data_operations_scheduler_install_dry_run", manifest
assert manifest["install_mode"] == "dry_run", manifest
assert manifest["scheduler_activation"] == "not_installed", manifest
assert manifest["scheduler_type"] == "launchd", manifest
assert manifest["job_id"] == "macro-weekly", manifest
assert manifest["pipeline_name"] == "macro_upsert", manifest
assert Path(manifest["env_file"]).resolve() == Path(env_file).resolve(), manifest
assert manifest["host_install_path_written"] is False, manifest
assert Path(manifest["output_dir"]).is_dir(), manifest
assert plist_path.is_file(), manifest

with open(plist_path, "rb") as handle:
    plist = plistlib.load(handle)

assert plist["Label"] == "com.stockanalysis.data-operations.macro-weekly", plist
assert plist["WorkingDirectory"] == root_dir, plist
assert plist["RunAtLoad"] is False, plist
assert plist["ProgramArguments"][0] == "/bin/bash", plist
assert plist["ProgramArguments"][1] == "-lc", plist
command = plist["ProgramArguments"][2]
assert "scripts/run_data_operations_scheduler_job.sh" in command, plist
assert f"--env-file {manifest['env_file']}" in command, plist
assert "--job-id macro-weekly" in command, plist
assert "--timeout-seconds 120" in command, plist
assert "macro-batch-upsert" in command, plist
assert plist["StartCalendarInterval"] == [{"Weekday": 2, "Hour": 7, "Minute": 30}], plist
assert plist["StandardOutPath"].endswith(".stdout.log"), plist
assert plist["StandardErrorPath"].endswith(".stderr.log"), plist

text = json.dumps({"manifest": manifest, "plist": plist})
for forbidden in [
    "postgresql://",
    "fred-runtime-token",
    "alpha-runtime-token",
    "openai-runtime-key",
    "secret-value",
]:
    assert forbidden not in text, forbidden
PY

case "$MANIFEST_PATH" in
  "$HOME/Library/LaunchAgents/"*)
    echo "Dry-run rendered to host scheduler directory: $MANIFEST_PATH" >&2
    exit 1
    ;;
esac

for activation_path in \
  ".github/workflows/data-operations-scheduler.yml" \
  "cron/data-operations.cron" \
  "launchd/com.stockanalysis.data-operations.plist" \
  "$HOME/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"
do
  if [ -e "$activation_path" ]; then
    echo "Unexpected scheduler activation artifact exists: $activation_path" >&2
    exit 1
  fi
done

test -f docs/data-operations-scheduler-install-dry-run.md
test -f docs/plans/2026-05-06-data-operations-scheduler-install-dry-run.md
test -f docs/tasks/data-operations-scheduler-install-dry-run/contract.md
test -f docs/tasks/data-operations-scheduler-install-dry-run/plan.md
test -f docs/tasks/data-operations-scheduler-install-dry-run/handoff.md
test -f docs/tasks/data-operations-scheduler-install-dry-run/review.md

grep -q "render_data_operations_scheduler_install.sh" docs/data-operations-scheduler-install-dry-run.md
grep -q "data-operations-scheduler-install-dry-run" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-alert-boundary" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-activation-runbook" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-operator-dry-run" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-activation-approval-gate" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-request" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-user-decision" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-final-preflight" docs/project-execution-roadmap.md
grep -q "verify_data_operations_scheduler_install_dry_run.sh" docs/verification-plan.md
grep -q "docs/data-operations-scheduler-install-dry-run.md" README.md
grep -q 'Current task: `manual-host-scheduler-activation-explicit-approval`' docs/project-execution-roadmap.md
grep -q '현재 고정된 immediate next task는 `manual-host-scheduler-activation-explicit-approval`' AGENTS.md

PYTHONPATH=/Users/woody/ai/agent-work-harness/src "$PYTHON_BIN" -m awh verify --repo "$ROOT_DIR" --task data-operations-scheduler-install-dry-run

echo "data operations scheduler install dry-run verification passed"
