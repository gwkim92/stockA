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

bash -n scripts/verify_recommendation_weight_review_prospective_evidence_live_observation_v1.sh

"$PYTHON_BIN" -m compileall -q \
  src/stockanalysis/operations/recommendation_weight_review_prospective_evidence_live_observation_contract.py \
  src/stockanalysis/operations/recommendation_weight_review_prospective_evidence_live_observation.py \
  src/stockanalysis/operations/recommendation_weight_review_prospective_evidence_live_observation_cli.py \
  tests/test_recommendation_weight_review_prospective_evidence_live_observation.py

"$PYTHON_BIN" -m unittest \
  tests.test_recommendation_weight_review_prospective_evidence_live_observation -v

HELP_FILE="$(mktemp)"
trap 'rm -f "$HELP_FILE"' EXIT
"$PYTHON_BIN" -m \
  stockanalysis.operations.recommendation_weight_review_prospective_evidence_live_observation_cli \
  --help >"$HELP_FILE"

for required in \
  --as-of-date \
  --lineage-eval-run-id \
  --portfolio-feedback-calibration-eval-run-id \
  --portfolio-name \
  --environment-label \
  --expected-database-identity-sha256 \
  --execute; do
  grep -F -- "$required" "$HELP_FILE" >/dev/null
done

if grep -E -- '--(approve|authorize|pilot|weight-delta|component-weight|recommended-weight|order|broker|rebalance|deploy|migrate)' "$HELP_FILE" >/dev/null; then
  echo "unsafe authorization or mutation flag exposed by live observation CLI" >&2
  exit 1
fi

"$PYTHON_BIN" - <<'PY'
from datetime import date

from stockanalysis.operations.recommendation_weight_review_prospective_evidence_live_observation import (
    DATABASE_IDENTITY_CONTRACT_VERSION,
    normalize_live_observation_database_identity,
    render_live_observation_database_identity_sql,
    render_live_observation_eval_insert_sql,
    render_live_observation_guarded_bundle_lookup_sql,
    render_live_observation_pipeline_run_insert_sql,
    render_live_observation_pipeline_run_status_sql,
)

identity_sql = render_live_observation_database_identity_sql().lower()
for required in (
    "live observation database identity v1",
    "current_database()",
    "current_user",
    "to_regclass('ai.eval_run')",
    "to_regclass('ops.pipeline_run')",
    "to_regclass('signal.recommendation')",
    "to_regclass('signal.recommendation_score_component')",
    "to_regclass('performance.recommendation_outcome')",
):
    assert required in identity_sql, required
for prohibited in ("insert into", "update ", "delete from", "truncate "):
    assert prohibited not in identity_sql, prohibited

identity = normalize_live_observation_database_identity(
    {
        "contract_version": DATABASE_IDENTITY_CONTRACT_VERSION,
        "database_name": "stockanalysis",
        "role_name": "stockanalysis_app",
        "server_version_num": "160004",
        "server_address": "127.0.0.1",
        "server_port": 5432,
        "required_relations": {
            "ai.eval_run": True,
            "ops.pipeline_run": True,
            "performance.recommendation_outcome": True,
            "portfolio.portfolio": True,
            "signal.recommendation": True,
            "signal.recommendation_batch": True,
            "signal.recommendation_score_component": True,
        },
    }
)
assert identity["complete"] is True
assert len(str(identity["sha256"])) == 64

lookup_sql = render_live_observation_guarded_bundle_lookup_sql(
    as_of_date=date(2026, 7, 15),
    lineage_eval_run_id=501,
    portfolio_feedback_calibration_eval_run_id=601,
    portfolio_name="Long Term Paper",
    database_identity=identity,
).lower()
for required in (
    "do $stockanalysis_live_observation_guard$",
    "current_database() = 'stockanalysis'",
    "current_user::text = 'stockanalysis_app'",
    "to_regclass('signal.recommendation') is not null",
    "prospective evidence foundation v1 atomic lookup",
    "eval_run.eval_run_id = 501",
    "eval_run.eval_run_id = 601",
):
    assert required in lookup_sql, required
for prohibited in ("insert into", "update ", "delete from", "truncate "):
    assert prohibited not in lookup_sql, prohibited

write_statements = (
    render_live_observation_pipeline_run_insert_sql(
        config_json={"mode": "test"},
        database_identity=identity,
    ),
    render_live_observation_eval_insert_sql(
        score_json={"status": "live_observation_complete_fresh_read_only"},
        database_identity=identity,
    ),
    render_live_observation_pipeline_run_status_sql(
        run_id=99,
        status="succeeded",
        database_identity=identity,
    ),
)
for statement in write_statements:
    lowered = statement.lower()
    assert "current_database() = 'stockanalysis'" in lowered
    assert "current_user::text = 'stockanalysis_app'" in lowered
    assert "to_regclass('signal.recommendation') is not null" in lowered

insert_sql = write_statements[1].lower()
assert insert_sql.count("insert into") == 1
assert "insert into ai.eval_run" in insert_sql
for prohibited in (
    "delete from",
    "portfolio.position",
    "broker.",
    "postgresql://",
    "password",
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
    "recommendation_weight_review_prospective_evidence_live_observation_cli:main_entry"
)
actual = project["project"]["scripts"].get(
    "stockanalysis-weight-prospective-evidence-live-observation"
)
if actual != expected:
    raise SystemExit(f"live observation entry point mismatch: {actual!r}")
PY

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git diff --check
  if git rev-parse --verify develop >/dev/null 2>&1; then
    MERGE_BASE="$(git merge-base HEAD develop)"
    if git diff --name-only "$MERGE_BASE" HEAD -- db/migrations | grep -q .; then
      echo "live observation task must not modify db/migrations" >&2
      exit 1
    fi
  fi
fi

echo "recommendation weight review prospective evidence live observation v1 verification passed"
