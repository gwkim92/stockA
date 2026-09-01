#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
else
  PYTHON_BIN="${PYTHON_BIN:-python3}"
fi

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

"$PYTHON_BIN" -m compileall -q \
  src/stockanalysis/operations/recommendation_weight_review_source_lineage_reconciliation.py \
  src/stockanalysis/operations/recommendation_weight_review_source_lineage_reconciliation_cli.py \
  tests/test_recommendation_weight_review_source_lineage_reconciliation.py

"$PYTHON_BIN" -m unittest \
  tests.test_recommendation_weight_review_source_lineage_reconciliation -v

HELP_FILE="$(mktemp)"
trap 'rm -f "$HELP_FILE"' EXIT
"$PYTHON_BIN" -m \
  stockanalysis.operations.recommendation_weight_review_source_lineage_reconciliation_cli \
  --help >"$HELP_FILE"

for required in --as-of-date --readiness-eval-run-id --execute; do
  grep -F -- "$required" "$HELP_FILE" >/dev/null
done

if grep -E -- '--(approve|authorize|pilot|weight-delta|component-weight|order|broker)' "$HELP_FILE" >/dev/null; then
  echo "unsafe authorization or mutation flag exposed by lineage reconciliation CLI" >&2
  exit 1
fi

"$PYTHON_BIN" - <<'PY'
from datetime import date

from stockanalysis.operations.recommendation_weight_review_source_lineage_reconciliation import (
    render_source_lineage_bundle_lookup_sql,
    render_source_lineage_reconciliation_eval_insert_sql,
)

lookup = render_source_lineage_bundle_lookup_sql(
    as_of_date=date(2026, 7, 11),
    readiness_eval_run_id=401,
).lower()
assert "referenced_quality" in lookup
assert "referenced_outcome" in lookup
assert "latest_quality" in lookup
assert "latest_outcome" in lookup
for prohibited in ("insert into", "update ", "delete from"):
    assert prohibited not in lookup, prohibited

insert_sql = render_source_lineage_reconciliation_eval_insert_sql(
    score_json={"status": "reconciled_read_only"}
).lower()
assert insert_sql.count("insert into") == 1
assert "insert into ai.eval_run" in insert_sql
for prohibited in (
    "update ",
    "delete from",
    "signal.recommendation",
    "portfolio.position",
    "broker.",
):
    assert prohibited not in insert_sql, prohibited
PY

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git diff --check
  if git rev-parse --verify develop >/dev/null 2>&1; then
    MERGE_BASE="$(git merge-base HEAD develop)"
    if git diff --name-only "$MERGE_BASE" HEAD -- db/migrations | grep -q .; then
      echo "lineage reconciliation task must not modify db/migrations" >&2
      exit 1
    fi
  fi
fi

echo "recommendation weight review source lineage reconciliation v1 verification passed"
