# Evaluation history completion implementation plan

**Goal:** Finish the outstanding evaluation history workflow and retire all completed feature branches.

**Architecture:** Keep the frozen history reader isolated from mutable source tables. Add a separate bounded comparison endpoint and independently verify hashes on returned snapshots; build server-rendered history list/detail routes reusing the existing design system. Integrate the already verified PR #49 and the completed follow-up into develop using the authorized repository SSH identity.

**Tech Stack:** Python/FastAPI/PostgreSQL, Next.js/TypeScript, unittest, Vitest, Playwright.

1. Backup and integration: validate `.git/stocka-before-branch-cleanup-2026-09-08.bundle`, fast-forward remote develop to verified PR #49 head, record proof for each branch and delete only exact verified heads. Preserve main/develop and the active task.
2. Reader tests: create `tests/test_evaluation_history_completion.py` covering canonical hash matches/mismatches, comparison selectors, preserved history, current missing sources and later same-horizon outcomes. Add actual PG coverage in a dedicated disposable test schema/DB.
3. Backend: add `src/stockanalysis/frontend/recommendation_eval_comparison.py`; wire explicit comparison dispatch in `api_adapter.py`. Add hash metadata to existing history detail without changing stored state or historical payload. Use the same canonical serialization as the writer and report unverifiable data explicitly.
4. UI: add `/performance/evaluations` list and `/performance/evaluations/[runId]` detail, isolated data loader/types and shared rendering/styles. Preserve IDs as strings, handle bad inputs before IO, paginate, link from performance navigation, show recorded-versus-current fields and dated same-horizon outcomes.
5. Verification: Python reader/HTTP/CLI regression; disposable PostgreSQL writes/reads and frozen-state checks; frontend model tests, build/type, desktop/tablet/mobile interaction tests and screenshots. Follow visual-qa two independent read-only reviewer passes while completing useful local checks.
6. Finish: record evidence and known runtime limits, review diff, commit/push to develop after checks, verify remote state, remove the completed local task branch and refresh the branch inventory.
