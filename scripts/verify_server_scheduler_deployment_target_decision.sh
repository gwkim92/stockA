#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

bash -n scripts/verify_server_scheduler_deployment_target_decision.sh
python3 -m compileall \
  src/stockanalysis/operations/server_scheduler_deployment_decision.py \
  src/stockanalysis/operations/cli.py \
  tests/test_server_scheduler_deployment_decision.py \
  tests/test_data_operations_cli.py >/dev/null

PYTHONPATH=src python3 -m unittest \
  tests.test_server_scheduler_deployment_decision \
  tests.test_data_operations_cli.DataOperationsCliTests.test_server_scheduler_deployment_target_decision_command_writes_output_and_markdown \
  tests.test_data_operations_cli.DataOperationsCliTests.test_server_scheduler_deployment_target_decision_rejects_repo_inside_output

TMP_ROOT=$(mktemp -d /tmp/stockanalysis-scheduler-decision.XXXXXX)
trap 'rm -rf "$TMP_ROOT"' EXIT

PYTHONPATH=src python3 -m stockanalysis.operations.cli server-scheduler-deployment-target-decision \
  --repo-root "$ROOT_DIR" \
  --repo-visibility public \
  --output "$TMP_ROOT/server-scheduler-deployment-target-decision.json" \
  --markdown-output "$TMP_ROOT/server-scheduler-deployment-target-decision.md" >/dev/null

python3 - "$TMP_ROOT/server-scheduler-deployment-target-decision.json" "$TMP_ROOT/server-scheduler-deployment-target-decision.md" <<'PY'
import json
import sys

report_path, markdown_path = sys.argv[1], sys.argv[2]
report_text = open(report_path, encoding="utf-8").read()
markdown = open(markdown_path, encoding="utf-8").read()
report = json.loads(report_text)
combined = report_text + markdown

assert report["report_name"] == "server_scheduler_deployment_target_decision"
assert report["decision_status"] == "blocked_missing_hosted_database_or_runtime"
assert report["recommended_target"] == "github_actions_scheduled_workflow_after_hosted_runtime"
assert report["scheduler_deployed"] is False
assert report["scheduler_deployment_allowed_in_this_task"] is False
assert report["host_mutation_allowed"] is False
assert report["workflow_file_created"] is False
assert "external_scheduler_cannot_reach_current_local_postgres" in report["blocking_reasons"]
assert "postgresql://" not in combined
assert "api-key" not in combined.lower()
assert "bearer " not in combined.lower()
assert "launchctl bootstrap" not in combined
assert "kubectl apply" not in combined
assert "Server Scheduler Deployment Target Decision" in markdown
print("server scheduler deployment target decision verification passed")
PY

test -f docs/tasks/server-scheduler-deployment-target-decision/contract.md
test -f docs/tasks/server-scheduler-deployment-target-decision/plan.md
test -f docs/plans/2026-05-20-server-scheduler-deployment-target-decision.md
test -f docs/server-scheduler-deployment-target-decision.md
