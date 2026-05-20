#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

bash -n scripts/verify_server_scheduler_invocation_boundary.sh
python3 -m compileall \
  src/stockanalysis/operations/server_scheduler_invocation.py \
  src/stockanalysis/operations/cli.py \
  tests/test_server_scheduler_invocation.py \
  tests/test_data_operations_cli.py >/dev/null

PYTHONPATH=src python3 -m unittest \
  tests.test_server_scheduler_invocation \
  tests.test_data_operations_cli.DataOperationsCliTests.test_server_scheduler_invocation_plan_command_writes_output_and_markdown \
  tests.test_data_operations_cli.DataOperationsCliTests.test_server_scheduler_invocation_plan_rejects_repo_inside_env

TMP_ROOT=$(mktemp -d /tmp/stockanalysis-server-scheduler.XXXXXX)
trap 'rm -rf "$TMP_ROOT"' EXIT

mkdir -p "$TMP_ROOT/artifacts"
cat >"$TMP_ROOT/data-operations.env" <<EOF
STOCKANALYSIS_DATABASE_URL="postgresql://user:hidden-server-scheduler-pass@localhost/db"
STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="$TMP_ROOT/artifacts"
EOF

PYTHONPATH=src python3 -m stockanalysis.operations.cli server-scheduler-invocation-plan \
  --repo-root "$ROOT_DIR" \
  --target cron \
  --schedule "30 18 * * 1-5" \
  --runtime-root "$TMP_ROOT/runtime" \
  --data-operations-env-file "$TMP_ROOT/data-operations.env" \
  --worker-output "$TMP_ROOT/local-ingest-worker.json" \
  --smoke-output "$TMP_ROOT/manual-local-ingest-smoke.json" \
  --artifact-root "$TMP_ROOT/artifacts" \
  --job-id market-price-daily \
  --python-executable /usr/bin/python3 \
  --output "$TMP_ROOT/server-scheduler-invocation.json" \
  --markdown-output "$TMP_ROOT/server-scheduler-invocation.md" >/dev/null

python3 - "$TMP_ROOT/server-scheduler-invocation.json" "$TMP_ROOT/server-scheduler-invocation.md" <<'PY'
import json
import sys

report_path, markdown_path = sys.argv[1], sys.argv[2]
report_text = open(report_path, encoding="utf-8").read()
markdown = open(markdown_path, encoding="utf-8").read()
report = json.loads(report_text)
combined = report_text + markdown

assert report["report_name"] == "server_scheduler_invocation_boundary"
assert report["scheduler_target"] == "cron"
assert report["scheduler_deployed"] is False
assert report["scheduler_install_allowed_in_this_task"] is False
assert report["host_mutation_allowed"] is False
assert report["launchctl_executed"] is False
assert report["child_command_executed"] is False
assert report["worker_execute"] is False
assert "local-ingest-worker-run" in report["shell_command_preview"]
assert "--execute" not in report["command_argv_preview"]
assert report["target_manifest_preview"]["kind"] == "crontab_line_preview"
assert "hidden-server-scheduler-pass" not in combined
assert "postgresql://" not in combined
assert "launchctl bootstrap" not in combined
assert "Server Scheduler Invocation Boundary" in markdown
print("server scheduler invocation boundary verification passed")
PY

test -f docs/tasks/server-scheduler-invocation-boundary/contract.md
test -f docs/tasks/server-scheduler-invocation-boundary/plan.md
test -f docs/plans/2026-05-20-server-scheduler-invocation-boundary.md
test -f docs/server-scheduler-invocation-boundary.md
