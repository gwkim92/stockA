#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$ROOT_DIR"

bash -n scripts/verify_internal_rag_retrieval_foundation_v1.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/ai/internal_rag.py \
  src/stockanalysis/frontend/live_adapter.py \
  src/stockanalysis/operations/cli.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_internal_rag \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_ai_evidence_neighborhood_response_matches_contract_shape \
  tests.test_data_operations_cli.DataOperationsCliTests.test_internal_rag_context_command_prints_read_only_context \
  tests.test_data_operations_cli.DataOperationsCliTests.test_internal_rag_context_command_writes_repo_outside_output \
  -v

test -f docs/tasks/internal-rag-retrieval-foundation-v1/contract.md
test -f docs/tasks/internal-rag-retrieval-foundation-v1/handoff.md
test -f docs/tasks/internal-rag-retrieval-foundation-v1/review.md

grep -q "build_internal_rag_context_package" src/stockanalysis/ai/internal_rag.py
grep -q "internal_rag_context" src/stockanalysis/frontend/live_adapter.py
grep -q "internal-rag-context-run" src/stockanalysis/operations/cli.py
grep -q "internal_rag_context" apps/web/src/lib/types.ts
grep -q "AI가 이 종목을 다시 분석할 때 참고하는 자료" 'apps/web/src/app/stocks/[symbol]/page.tsx'
grep -q "verify_internal_rag_retrieval_foundation_v1.sh" docs/verification-plan.md
grep -q "vector_storage_uri" tests/test_internal_rag.py
grep -q "self.assertNotIn(\"vector_storage_uri\"" tests/test_internal_rag.py

echo "internal RAG retrieval foundation verification passed"
