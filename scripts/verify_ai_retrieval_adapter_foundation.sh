#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$ROOT_DIR"

bash -n scripts/verify_ai_retrieval_adapter_foundation.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/ai/__init__.py \
  src/stockanalysis/ai/retrieval.py \
  src/stockanalysis/ai/evidence_graph.py \
  src/stockanalysis/ai/ontology_validation.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_ai_retrieval \
  tests.test_ai_evidence_graph \
  tests.test_ai_ontology_validation \
  -v

test -f docs/tasks/ai-retrieval-adapter-foundation/contract.md
test -f docs/tasks/ai-retrieval-adapter-foundation/plan.md
test -f docs/tasks/ai-retrieval-adapter-foundation/handoff.md
test -f docs/tasks/ai-retrieval-adapter-foundation/review.md

grep -q "class RetrievalQuery" src/stockanalysis/ai/retrieval.py
grep -q "class RetrievalResult" src/stockanalysis/ai/retrieval.py
grep -q "class InMemoryRetrievalAdapter" src/stockanalysis/ai/retrieval.py
grep -q "render_instrument_evidence_neighborhood_sql" src/stockanalysis/ai/evidence_graph.py
grep -q "ref.classification_node" src/stockanalysis/ai/evidence_graph.py
grep -q "event.event_classification_impact" src/stockanalysis/ai/evidence_graph.py
grep -q "ai.embedding_index" src/stockanalysis/ai/evidence_graph.py
grep -q "render_ontology_lite_validation_sql" src/stockanalysis/ai/ontology_validation.py
grep -q "inferred_membership_without_evidence" src/stockanalysis/ai/ontology_validation.py
grep -q "overlapping_classification_edge_window" src/stockanalysis/ai/ontology_validation.py
grep -q "verify_ai_retrieval_adapter_foundation.sh" docs/verification-plan.md

echo "ai retrieval adapter foundation verification passed"
