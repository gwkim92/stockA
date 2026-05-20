# Implementation Plan

1. Create a task contract and handoff for `ai-retrieval-adapter-foundation`.
2. Add retrieval query/result dataclasses and a deterministic in-memory adapter.
3. Add Postgres evidence neighborhood SQL that uses canonical `ref`, `event`, `ai`, `signal`, and `portfolio` tables.
4. Add ontology-lite validation SQL for classification edge and membership consistency.
5. Add targeted unit tests and a verification script.
6. Record exact verification results and residual risks.

## Boundaries

- Do not add vector DB, graph DB, pgvector, OpenAI vector store, Neo4j, RDF, SHACL, or orchestration dependencies.
- Do not change DB schema, recommendation scoring, benchmark, evaluation split, frontend routes, or trading flow.
- Keep all SQL renderers read-only.
