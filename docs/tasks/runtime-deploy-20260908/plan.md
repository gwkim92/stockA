# Execution plan

1. Read sanitized recent pipeline/AI failures, runtime versions/service configuration, schema state and current resources.
2. Preserve DB dump, current commit/build/dependencies/config metadata and task-owned timer state. Rehearse additive migration on disposable local database if needed; pre-existing CI/PG tests already validate its structure.
3. Update server develop to tested application commit, install dependencies, build under bounded memory with reversible temporary swap, apply only missing migration 0035 transactionally, restart affected services. Keep rollback artifacts.
4. Verify readiness, authenticated evaluation API contracts, existing routes and rendered live pages. Inspect actual scheduler results and freshness failures; perform only evidence-supported recovery.
5. Record deployed commit, backup paths, outcomes, unresolved blockers and exact next steps. Preserve unrelated server dogfood-output/ files.
