#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

bash -n scripts/verify_frontend_api_observability_sink_decision.sh
python3 -m compileall src tests >/dev/null

test -f docs/frontend-api-observability-sink-decision.md
test -f docs/plans/2026-05-03-frontend-api-observability-sink-decision.md
test -f docs/tasks/frontend-api-observability-sink-decision/contract.md
test -f docs/tasks/frontend-api-observability-sink-decision/plan.md
test -f docs/tasks/frontend-api-observability-sink-decision/handoff.md
test -f docs/tasks/frontend-api-observability-sink-decision/review.md

grep -q "OpenTelemetry Collector" docs/frontend-api-observability-sink-decision.md
grep -q "OTLP" docs/frontend-api-observability-sink-decision.md
grep -q "Loki" docs/frontend-api-observability-sink-decision.md
grep -q "Prometheus" docs/frontend-api-observability-sink-decision.md
grep -q "Alertmanager" docs/frontend-api-observability-sink-decision.md
grep -q "Forbidden labels" docs/frontend-api-observability-sink-decision.md
grep -q "request id" docs/frontend-api-observability-sink-decision.md
grep -q "raw query string" docs/frontend-api-observability-sink-decision.md
grep -q "DB URL" docs/frontend-api-observability-sink-decision.md
grep -q "frontend-api-otel-exporter-pilot" docs/frontend-api-observability-sink-decision.md
grep -q "frontend-api-observability-sink-decision" docs/project-execution-roadmap.md
grep -q "frontend-api-otel-exporter-pilot" docs/project-execution-roadmap.md
grep -q "frontend-api-local-collector-smoke" docs/project-execution-roadmap.md
grep -q "frontend-api-alert-rules" docs/project-execution-roadmap.md
grep -q "data-operations-cadence-foundation" docs/project-execution-roadmap.md
grep -q "data-operations-artifact-runner" docs/project-execution-roadmap.md
grep -q '현재 고정된 immediate next task는 `data-operations-runtime-env-readiness`' AGENTS.md
grep -q "verify_frontend_api_observability_sink_decision.sh" docs/verification-plan.md
grep -q "docs/frontend-api-observability-sink-decision.md" README.md

echo "frontend API observability sink decision verification passed"
