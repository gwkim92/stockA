# Implementation Plan

1. Create task contract, handoff, and implementation plan for `ai-retrieval-graph-foundation`.
2. Add a current implementation status section to `docs/ai-intelligence-architecture.md`.
3. Add roadmap notes under AI Runtime without changing the immediate next task.
4. Write a standalone implementation plan in `docs/plans/2026-05-03-ai-retrieval-graph-foundation.md`.
5. Run lightweight documentation verification.
6. Record verification and residual risks in `handoff.md` or `review.md`.

## Future Implementation Sequence

1. Freeze retrieval DTO names and internal module boundary.
2. Write failing unit tests for graph neighborhood query rendering.
3. Implement minimal Postgres graph neighborhood SQL using existing `ref`, `event`, `signal`, and `portfolio` tables.
4. Write failing unit tests for vector adapter interface behavior with an in-memory fake.
5. Implement vector adapter interface without selecting production backend.
6. Add ontology-lite validation SQL checks for orphan edges, invalid relation types, missing evidence, and overlapping validity windows.
7. Add Docker smoke only after schema/runtime scope is explicit.
8. Update `docs/verification-plan.md` when a real runtime or schema change exists.

## Do Not Do In This Task

- Do not add Dagster, Prefect, Airflow, Neo4j, RDF, SHACL, pgvector, or OpenAI vector store dependencies.
- Do not change recommendation scoring, benchmark, evaluation split, or portfolio action policy.
- Do not add frontend product routes before backend evidence/retrieval contracts exist.
- Do not change the active immediate next task.
