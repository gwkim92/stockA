#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"
cd "$ROOT_DIR"

bash -n scripts/verify_frontend_api_alert_rules.sh
"$PYTHON_BIN" -m py_compile scripts/validate_frontend_api_alert_rules.py
"$PYTHON_BIN" scripts/validate_frontend_api_alert_rules.py ops/observability/frontend-api-alert-rules.yml

test -f ops/observability/frontend-api-alert-rules.yml
test -f docs/frontend-api-alert-rules.md
test -f docs/plans/2026-05-03-frontend-api-alert-rules.md
test -f docs/tasks/frontend-api-alert-rules/contract.md
test -f docs/tasks/frontend-api-alert-rules/plan.md
test -f docs/tasks/frontend-api-alert-rules/handoff.md
test -f docs/tasks/frontend-api-alert-rules/review.md

grep -q "FrontendApiDown" ops/observability/frontend-api-alert-rules.yml
grep -q "FrontendApiNotReady" ops/observability/frontend-api-alert-rules.yml
grep -q "FrontendApiHigh5xxRate" ops/observability/frontend-api-alert-rules.yml
grep -q "FrontendApiTimeoutSpike" ops/observability/frontend-api-alert-rules.yml
grep -q "FrontendApiHighLatency" ops/observability/frontend-api-alert-rules.yml
grep -q "FrontendApiAdapterErrorSpike" ops/observability/frontend-api-alert-rules.yml
grep -q "Alertmanager receiver" docs/frontend-api-alert-rules.md
grep -q "frontend_api_requests_total" docs/frontend-api-alert-rules.md
grep -q "ops/observability/frontend-api-alert-rules.yml" README.md
grep -q "frontend-api-alert-rules" docs/project-execution-roadmap.md
grep -q "data-operations-cadence-foundation" docs/project-execution-roadmap.md
grep -q "data-operations-artifact-runner" docs/project-execution-roadmap.md
grep -q '현재 고정된 immediate next task는 `data-operations-runtime-env-readiness`' AGENTS.md
grep -q "verify_frontend_api_alert_rules.sh" docs/verification-plan.md

echo "frontend API alert rules verification passed"
