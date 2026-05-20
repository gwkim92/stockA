#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

bash -n scripts/verify_local_ingest_worker_data_health_visibility.sh
python3 -m compileall \
  src/stockanalysis/operations/local_ingest_worker.py \
  src/stockanalysis/frontend/live_adapter.py \
  tests/test_local_ingest_worker.py \
  tests/test_frontend_live_adapter.py >/dev/null

PYTHONPATH=src python3 -m unittest \
  tests.test_local_ingest_worker \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_data_health_response_matches_frontend_contract_shape \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_data_health_response_includes_sanitized_local_ingest_worker

cd apps/web
npm run typecheck
cd "$ROOT_DIR"

grep -q "local_ingest_worker" docs/api/frontend/examples/data-health.json
grep -q "로컬 worker 실행 증거" apps/web/src/app/data-health/page.tsx
grep -q "STOCKANALYSIS_LOCAL_INGEST_WORKER_REPORT" src/stockanalysis/operations/local_ingest_worker.py
grep -q "local-ingest-worker-data-health-visibility" docs/project-execution-roadmap.md

echo "local ingest worker data-health visibility verification passed"
