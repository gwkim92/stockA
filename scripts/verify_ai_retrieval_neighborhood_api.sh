#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$ROOT_DIR"

bash -n scripts/verify_ai_retrieval_neighborhood_api.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/ai/evidence_graph.py \
  src/stockanalysis/frontend/live_adapter.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_ai_evidence_graph \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_ai_evidence_neighborhood_response_matches_contract_shape \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_ai_evidence_neighborhood_sql_uses_read_only_foundation_renderer \
  -v

test -f docs/tasks/ai-retrieval-neighborhood-api/contract.md
test -f docs/tasks/ai-retrieval-neighborhood-api/handoff.md
test -f docs/tasks/ai-retrieval-neighborhood-api/review.md

grep -q "/api/ai/evidence-neighborhoods/" src/stockanalysis/frontend/live_adapter.py
grep -q "render_instrument_evidence_neighborhood_sql" src/stockanalysis/frontend/live_adapter.py
grep -q "vector_storage_uri" src/stockanalysis/ai/evidence_graph.py
grep -q "vector_storage_uri" tests/test_frontend_live_adapter.py
grep -q "self.assertNotIn(\"vector_storage_uri\"" tests/test_frontend_live_adapter.py
grep -q "getAiEvidenceNeighborhood" apps/web/src/lib/frontend-api.ts
grep -q "AiEvidenceNeighborhoodData" apps/web/src/lib/types.ts
grep -q "AI 증거 관계망" 'apps/web/src/app/stocks/[symbol]/page.tsx'
grep -q "verify_ai_retrieval_neighborhood_api.sh" docs/verification-plan.md

echo "ai retrieval neighborhood API verification passed"
