# Review

## Summary

- Added `src/stockanalysis/ai/` as the internal AI retrieval/graph boundary.
- Added deterministic retrieval DTOs and `InMemoryRetrievalAdapter` for local/free tests.
- Added read-only Postgres evidence neighborhood SQL for instrument-centered graph context.
- Added read-only ontology-lite validation SQL for classification edge and inferred membership consistency checks.
- Added targeted tests and a verification script.

## Verification

- First targeted test run failed before implementation because the new modules did not exist.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_ai_retrieval tests.test_ai_evidence_graph tests.test_ai_ontology_validation -v`: 9 tests passed.
- `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_ai_retrieval_adapter_foundation.sh`: passed.

## Residual Risks

- No production vector DB, graph DB, pgvector, OpenAI vector store, or GraphRAG runtime was introduced.
- No live LLM call or embedding backfill was run.
- No recommendation scoring, benchmark, evaluation split, frontend route, or trading flow was changed.
- The next useful implementation unit is either a read-only API endpoint for evidence neighborhoods or a controlled embedding backfill pilot using existing `ai.document_chunk` metadata.
