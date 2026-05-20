#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

bash -n scripts/verify_hosted_database_runtime_decision.sh
python3 -m compileall \
  src/stockanalysis/operations/hosted_runtime_decision.py \
  src/stockanalysis/operations/cli.py \
  tests/test_hosted_runtime_decision.py \
  tests/test_data_operations_cli.py >/dev/null

PYTHONPATH=src python3 -m unittest \
  tests.test_hosted_runtime_decision \
  tests.test_data_operations_cli.DataOperationsCliTests.test_hosted_database_runtime_decision_command_writes_output_and_markdown \
  tests.test_data_operations_cli.DataOperationsCliTests.test_hosted_database_runtime_decision_rejects_repo_inside_output

TMP_ROOT=$(mktemp -d /tmp/stockanalysis-hosted-runtime.XXXXXX)
trap 'rm -rf "$TMP_ROOT"' EXIT

PYTHONPATH=src python3 -m stockanalysis.operations.cli hosted-database-runtime-decision \
  --repo-root "$ROOT_DIR" \
  --repo-visibility public \
  --output "$TMP_ROOT/hosted-database-runtime-decision.json" \
  --markdown-output "$TMP_ROOT/hosted-database-runtime-decision.md" >/dev/null

python3 - "$TMP_ROOT/hosted-database-runtime-decision.json" "$TMP_ROOT/hosted-database-runtime-decision.md" <<'PY'
import json
import sys

report_path, markdown_path = sys.argv[1], sys.argv[2]
report_text = open(report_path, encoding="utf-8").read()
markdown = open(markdown_path, encoding="utf-8").read()
report = json.loads(report_text)
combined = report_text + markdown

assert report["report_name"] == "hosted_database_runtime_decision"
assert report["decision_status"] == "setup_required_for_hosted_database"
assert report["recommended_path"] == "supabase_free_postgres_plus_github_actions_worker"
assert report["provisioning_performed"] is False
assert report["database_created"] is False
assert report["secret_written"] is False
assert report["workflow_file_created"] is False
assert "hosted_database_not_configured" in report["blocking_reasons"]
assert "postgresql://" not in combined
assert "api-key" not in combined.lower()
assert "bearer " not in combined.lower()
assert "sk-" not in combined.lower()
assert "supabase_free_postgres_plus_github_actions_worker" in combined
assert "Hosted Database Runtime Decision" in markdown
print("hosted database runtime decision verification passed")
PY

test -f docs/tasks/hosted-database-runtime-decision/contract.md
test -f docs/tasks/hosted-database-runtime-decision/plan.md
test -f docs/plans/2026-05-20-hosted-database-runtime-decision.md
test -f docs/hosted-database-runtime-decision.md
