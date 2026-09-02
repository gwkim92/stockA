#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

bash -n scripts/verify_analysis_integrity_ci.sh

"$PYTHON_BIN" -m compileall -q \
  src/stockanalysis/operations/recommendation_weight_review_source_lineage_reconciliation.py \
  src/stockanalysis/operations/recommendation_weight_review_source_lineage_reconciliation_cli.py \
  src/stockanalysis/operations/recommendation_weight_review_prospective_evidence_contract.py \
  src/stockanalysis/operations/recommendation_weight_review_prospective_evidence_recommendation.py \
  src/stockanalysis/operations/recommendation_weight_review_prospective_evidence_outcome.py \
  src/stockanalysis/operations/recommendation_weight_review_prospective_evidence_feedback.py \
  src/stockanalysis/operations/recommendation_weight_review_prospective_evidence_lookup.py \
  src/stockanalysis/operations/recommendation_weight_review_prospective_evidence_foundation.py \
  src/stockanalysis/operations/recommendation_weight_review_prospective_evidence_foundation_cli.py \
  src/stockanalysis/operations/recommendation_weight_review_readiness_semantics.py \
  src/stockanalysis/operations/recommendation_weight_review_readiness_audit.py \
  tests/test_recommendation_weight_review_source_lineage_reconciliation.py \
  tests/recommendation_weight_review_prospective_evidence_fixtures.py \
  tests/test_recommendation_weight_review_prospective_evidence_identity.py \
  tests/test_recommendation_weight_review_prospective_evidence_feedback.py \
  tests/test_recommendation_weight_review_prospective_evidence_runtime.py \
  tests/test_recommendation_weight_review_readiness_semantics.py \
  tests/test_recommendation_weight_review_readiness_audit.py

"$PYTHON_BIN" -m unittest \
  tests.test_recommendation_weight_review_source_lineage_reconciliation \
  tests.test_recommendation_weight_review_prospective_evidence_identity \
  tests.test_recommendation_weight_review_prospective_evidence_feedback \
  tests.test_recommendation_weight_review_prospective_evidence_runtime \
  tests.test_recommendation_weight_review_readiness_semantics \
  tests.test_recommendation_weight_review_readiness_audit -v

"$PYTHON_BIN" - <<'PY'
import tomllib
from pathlib import Path

with Path("pyproject.toml").open("rb") as handle:
    project = tomllib.load(handle)

scripts = project["project"]["scripts"]
required = {
    "stockanalysis-operations": "stockanalysis.operations.cli:main_entry",
    "stockanalysis-weight-lineage-reconciliation": (
        "stockanalysis.operations."
        "recommendation_weight_review_source_lineage_reconciliation_cli:main_entry"
    ),
    "stockanalysis-weight-prospective-evidence": (
        "stockanalysis.operations."
        "recommendation_weight_review_prospective_evidence_foundation_cli:main_entry"
    ),
}
for name, target in required.items():
    actual = scripts.get(name)
    if actual != target:
        raise SystemExit(f"entry point {name!r} mismatch: {actual!r}")
PY

"$PYTHON_BIN" - <<'PY'
from pathlib import Path

workflow = Path(".github/workflows/analysis-integrity.yml").read_text(encoding="utf-8")
required_fragments = (
    "pull_request:",
    "push:",
    "workflow_dispatch:",
    "permissions:\n  contents: read",
    "actions/checkout@v4",
    "actions/setup-python@v5",
    "bash scripts/verify_analysis_integrity_ci.sh",
)
for fragment in required_fragments:
    if fragment not in workflow:
        raise SystemExit(f"workflow fragment missing: {fragment!r}")

lowered = workflow.lower()
for prohibited in (
    "secrets.",
    "permissions: write",
    "contents: write",
    "id-token: write",
    "pull-requests: write",
    "aws-actions/",
    "docker build",
    "docker compose",
    "services:",
    "psql ",
    "broker",
    "order submit",
    "deploy",
):
    if prohibited in lowered:
        raise SystemExit(f"prohibited CI capability found: {prohibited!r}")
PY

git diff --check

echo "analysis integrity CI verification passed"
