#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$ROOT_DIR"

bash -n scripts/verify_ai_news_cluster_map.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/frontend/live_adapter.py \
  src/stockanalysis/frontend/pagination.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_ai_news_cluster_list_response_matches_contract_shape \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_ai_news_cluster_list_sql_is_read_only \
  -v

test -f docs/tasks/ai-news-cluster-map/contract.md
test -f docs/tasks/ai-news-cluster-map/handoff.md
test -f docs/tasks/ai-news-cluster-map/review.md
test -f docs/plans/2026-05-19-ai-news-cluster-map.md

grep -q "/api/ai/news-clusters" src/stockanalysis/frontend/live_adapter.py
grep -q "artifact.artifact_type = 'news_cluster_summary'" src/stockanalysis/frontend/live_adapter.py
grep -q "ai.document_chunk" src/stockanalysis/frontend/live_adapter.py
grep -q "ai.embedding_index" src/stockanalysis/frontend/live_adapter.py
grep -q "vector_storage_uri" tests/test_frontend_live_adapter.py
grep -q "self.assertNotIn(\"vector_storage_uri\"" tests/test_frontend_live_adapter.py
grep -q "AiNewsClusterListData" apps/web/src/lib/types.ts
grep -q "getAiNewsClusters" apps/web/src/lib/frontend-api.ts
grep -q "저장된 AI 뉴스 묶음" apps/web/src/app/intelligence/page.tsx
grep -q "verify_ai_news_cluster_map.sh" docs/verification-plan.md

echo "AI news cluster map verification passed"
