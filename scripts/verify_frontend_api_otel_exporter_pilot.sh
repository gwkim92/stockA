#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"
cd "$ROOT_DIR"

bash -n scripts/verify_frontend_api_otel_exporter_pilot.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/frontend/observability.py \
  src/stockanalysis/frontend/api_server.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_frontend_observability \
  tests.test_frontend_api_server \
  -v

grep -q "opentelemetry-api" pyproject.toml
grep -q "opentelemetry-sdk" pyproject.toml
grep -q "opentelemetry-exporter-otlp-proto-http" pyproject.toml
grep -q "opentelemetry-instrumentation-fastapi" pyproject.toml
grep -q "STOCKANALYSIS_FRONTEND_API_OBSERVABILITY_MODE" src/stockanalysis/frontend/observability.py
grep -q "STOCKANALYSIS_FRONTEND_API_OTLP_ENDPOINT" src/stockanalysis/frontend/observability.py
grep -q "route_template" src/stockanalysis/frontend/api_server.py
grep -q "status_class" src/stockanalysis/frontend/api_server.py

test -f docs/frontend-api-otel-exporter-pilot.md
test -f docs/plans/2026-05-03-frontend-api-otel-exporter-pilot.md
test -f docs/tasks/frontend-api-otel-exporter-pilot/contract.md
test -f docs/tasks/frontend-api-otel-exporter-pilot/plan.md
test -f docs/tasks/frontend-api-otel-exporter-pilot/handoff.md
test -f docs/tasks/frontend-api-otel-exporter-pilot/review.md

grep -q "OTLP" docs/frontend-api-otel-exporter-pilot.md
grep -q "disabled" docs/frontend-api-otel-exporter-pilot.md
grep -q "route_template" docs/frontend-api-otel-exporter-pilot.md
grep -q "frontend-api-sql-pagination-optimization" docs/frontend-api-otel-exporter-pilot.md
grep -q "frontend-api-otel-exporter-pilot" docs/project-execution-roadmap.md
grep -q "frontend-api-sql-pagination-optimization" docs/project-execution-roadmap.md
grep -q "docs/frontend-api-sql-pagination-optimization.md" README.md
grep -q "frontend-api-local-collector-smoke" docs/project-execution-roadmap.md
grep -q "docs/frontend-api-local-collector-smoke.md" README.md
grep -q "frontend-api-alert-rules" docs/project-execution-roadmap.md
grep -q "docs/frontend-api-alert-rules.md" README.md
grep -q "data-operations-cadence-foundation" docs/project-execution-roadmap.md
grep -q "data-operations-artifact-runner" docs/project-execution-roadmap.md
grep -q '현재 고정된 immediate next task는 `data-operations-runtime-env-readiness`' AGENTS.md
grep -q "verify_frontend_api_otel_exporter_pilot.sh" docs/verification-plan.md
grep -q "docs/frontend-api-otel-exporter-pilot.md" README.md

echo "frontend API OTLP exporter pilot verification passed"
