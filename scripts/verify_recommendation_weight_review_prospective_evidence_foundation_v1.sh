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

bash -n scripts/verify_recommendation_weight_review_prospective_evidence_foundation_v1.sh

"$PYTHON_BIN" -m compileall -q \
  src/stockanalysis/operations/recommendation_weight_review_prospective_evidence_contract.py \
  src/stockanalysis/operations/recommendation_weight_review_prospective_evidence_recommendation.py \
  src/stockanalysis/operations/recommendation_weight_review_prospective_evidence_outcome.py \
  src/stockanalysis/operations/recommendation_weight_review_prospective_evidence_feedback.py \
  src/stockanalysis/operations/recommendation_weight_review_prospective_evidence_lookup.py \
  src/stockanalysis/operations/recommendation_weight_review_prospective_evidence_foundation.py \
  src/stockanalysis/operations/recommendation_weight_review_prospective_evidence_foundation_cli.py \
  tests/recommendation_weight_review_prospective_evidence_fixtures.py \
  tests/test_recommendation_weight_review_prospective_evidence_identity.py \
  tests/test_recommendation_weight_review_prospective_evidence_feedback.py \
  tests/test_recommendation_weight_review_prospective_evidence_runtime.py

"$PYTHON_BIN" -m unittest \
  tests.test_recommendation_weight_review_prospective_evidence_identity \
  tests.test_recommendation_weight_review_prospective_evidence_feedback \
  tests.test_recommendation_weight_review_prospective_evidence_runtime -v

HELP_FILE="$(mktemp)"
trap 'rm -f "$HELP_FILE"' EXIT
"$PYTHON_BIN" -m \
  stockanalysis.operations.recommendation_weight_review_prospective_evidence_foundation_cli \
  --help >"$HELP_FILE"

for required in \
  --as-of-date \
  --lineage-eval-run-id \
  --portfolio-feedback-calibration-eval-run-id \
  --portfolio-name \
  --execute; do
  grep -F -- "$required" "$HELP_FILE" >/dev/null
done

if grep -E -- '--(approve|authorize|pilot|weight-delta|component-weight|recommended-weight|order|broker|rebalance)' "$HELP_FILE" >/dev/null; then
  echo "unsafe authorization or mutation flag exposed by prospective evidence CLI" >&2
  exit 1
fi

"$PYTHON_BIN" - <<'PY'
from datetime import date

from stockanalysis.operations.recommendation_weight_review_prospective_evidence_lookup import (
    render_prospective_evidence_bundle_lookup_sql,
    render_prospective_evidence_foundation_eval_insert_sql,
)

lookup = render_prospective_evidence_bundle_lookup_sql(
    as_of_date=date(2026, 7, 15),
    lineage_eval_run_id=501,
    portfolio_feedback_calibration_eval_run_id=601,
).lower()
for required in (
    "prospective evidence foundation v1 atomic lookup",
    "recommendation_weight_review_source_lineage_reconciliation_v1",
    "canonical_chain,quality,eval_run_id",
    "canonical_chain,outcome,eval_run_id",
    "signal.recommendation_score_component",
    "performance.recommendation_outcome",
    "portfolio_review_feedback_calibration",
    "portfolio_review_decision_outcome_feedback",
    "latest_feedback_runs",
):
    assert required in lookup, required
for prohibited in ("insert into", "update ", "delete from", "truncate "):
    assert prohibited not in lookup, prohibited

insert_sql = render_prospective_evidence_foundation_eval_insert_sql(
    score_json={"status": "foundation_complete_fresh_read_only"}
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

"$PYTHON_BIN" - <<'PY'
import tomllib
from pathlib import Path

with Path("pyproject.toml").open("rb") as handle:
    project = tomllib.load(handle)

expected = (
    "stockanalysis.operations."
    "recommendation_weight_review_prospective_evidence_foundation_cli:main_entry"
)
actual = project["project"]["scripts"].get(
    "stockanalysis-weight-prospective-evidence"
)
if actual != expected:
    raise SystemExit(f"prospective evidence entry point mismatch: {actual!r}")
PY

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git diff --check
  if git rev-parse --verify develop >/dev/null 2>&1; then
    MERGE_BASE="$(git merge-base HEAD develop)"
    if git diff --name-only "$MERGE_BASE" HEAD -- db/migrations | grep -q .; then
      echo "prospective evidence foundation must not modify db/migrations" >&2
      exit 1
    fi
  fi
fi

echo "recommendation weight review prospective evidence foundation v1 verification passed"
