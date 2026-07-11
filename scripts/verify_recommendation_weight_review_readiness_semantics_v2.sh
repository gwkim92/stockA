#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN=${PYTHON_BIN:-"$ROOT_DIR/.venv/bin/python"}

cd "$ROOT_DIR"

bash -n scripts/verify_recommendation_weight_review_readiness_semantics_v2.sh

rg -q 'DEFAULT_EVAL_NAME = "recommendation_weight_review_readiness_semantics_v2"' \
  src/stockanalysis/operations/recommendation_weight_review_readiness_semantics.py
rg -q 'DEFAULT_DATASET_VERSION = "recommendation-weight-review-readiness-semantics-v2"' \
  src/stockanalysis/operations/recommendation_weight_review_readiness_semantics.py
rg -q '"mode": "shadow_read_only"' \
  src/stockanalysis/operations/recommendation_weight_review_readiness_semantics.py
rg -q '"authoritative": False' \
  src/stockanalysis/operations/recommendation_weight_review_readiness_semantics.py

if rg -n -i '\b(update|delete from|truncate)\s+(signal\.|portfolio\.|trading\.|performance\.)' \
  src/stockanalysis/operations/recommendation_weight_review_readiness_semantics.py; then
  echo "shadow v2 contains a forbidden domain mutation" >&2
  exit 1
fi

"$PYTHON_BIN" -m compileall -q \
  src/stockanalysis/operations/recommendation_weight_review_readiness_semantics.py \
  src/stockanalysis/operations/cli.py \
  src/stockanalysis/frontend/live_adapter.py \
  tests/test_recommendation_weight_review_readiness_semantics.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_recommendation_weight_review_readiness_semantics \
  tests.test_recommendation_weight_review_readiness_audit \
  tests.test_manual_weight_review_calibration_report \
  tests.test_data_operations_cli.DataOperationsCliTests.test_recommendation_weight_review_readiness_semantics_v2_command_passes_source_ids_and_env \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_weight_review_semantics_v2_missing_payload_is_fail_closed \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_weight_review_semantics_v2_raw_permissions_cannot_escalate -v

PYTHONPATH=src "$PYTHON_BIN" -m stockanalysis.operations.cli \
  recommendation-weight-review-readiness-semantics-v2-run --help \
  | rg -q -- '--readiness-eval-run-id'

if PYTHONPATH=src "$PYTHON_BIN" -m stockanalysis.operations.cli \
  recommendation-weight-review-readiness-semantics-v2-run --help \
  | rg -q -- '--(approve|authorize|pilot|delta|weight-value|component-weight)'; then
  echo "shadow v2 CLI exposes a forbidden approval or mutation option" >&2
  exit 1
fi

git diff --exit-code -- db/migrations
git diff --check

echo "recommendation weight review readiness semantics v2 verification passed"
