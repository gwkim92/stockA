#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"
cd "$ROOT_DIR"

bash -n scripts/verify_frontend_api_local_collector_smoke.sh
"$PYTHON_BIN" -m py_compile \
  scripts/smoke_frontend_api_local_otlp_receiver.py \
  src/stockanalysis/frontend/observability.py \
  src/stockanalysis/frontend/api_server.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_frontend_observability \
  tests.test_frontend_api_server \
  -v

PYTHONPATH=src "$PYTHON_BIN" scripts/smoke_frontend_api_local_otlp_receiver.py --repo-root "$ROOT_DIR"

test -f docs/frontend-api-local-collector-smoke.md
test -f docs/plans/2026-05-03-frontend-api-local-collector-smoke.md
test -f docs/tasks/frontend-api-local-collector-smoke/contract.md
test -f docs/tasks/frontend-api-local-collector-smoke/plan.md
test -f docs/tasks/frontend-api-local-collector-smoke/handoff.md
test -f docs/tasks/frontend-api-local-collector-smoke/review.md

grep -q "OTLP" docs/frontend-api-local-collector-smoke.md
grep -q "/v1/traces" docs/frontend-api-local-collector-smoke.md
grep -q "instrumented=true" docs/frontend-api-local-collector-smoke.md
grep -q "frontend-api-alert-rules" docs/project-execution-roadmap.md
grep -q "docs/frontend-api-alert-rules.md" README.md
grep -q "data-operations-cadence-foundation" docs/project-execution-roadmap.md
grep -q "data-operations-artifact-runner" docs/project-execution-roadmap.md
grep -q '현재 고정된 immediate next task는 `data-operations-runtime-env-readiness`' AGENTS.md
grep -q "verify_frontend_api_local_collector_smoke.sh" docs/verification-plan.md
grep -q "docs/frontend-api-local-collector-smoke.md" README.md

echo "frontend API local Collector smoke verification passed"
