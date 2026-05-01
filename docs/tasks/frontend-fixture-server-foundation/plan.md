# Implementation Plan

## Steps

1. Create task contract, plan, handoff, and review docs.
2. Add `src/stockanalysis/frontend/fixture_server.py` as a standard-library read-only HTTP wrapper around the fixture adapter.
3. Add `stockanalysis-frontend-fixture-server` console script in `pyproject.toml`.
4. Add `tests/test_frontend_fixture_server.py` with local HTTP server smoke tests.
5. Add `scripts/verify_frontend_fixture_server.sh` for syntax, unit, contract, adapter, HTTP runtime, and boundary checks.
6. Add `docs/frontend-fixture-server.md`.
7. Update README, frontend docs, API contract docs, and verification plan.
8. Run final verification and record results in handoff/review.

## Design Decisions

- Use Python standard library `http.server` to avoid prematurely committing to FastAPI or another production API framework.
- Keep `docs/api/frontend/contract-index.json` as source of truth through `api_adapter.py`.
- Preserve read-only boundary. Future write endpoints require auth, actor identity, reason capture, and audit trail.
- Use exact path matching for now because contract examples encode query strings explicitly.

## Verification

```bash
bash -n scripts/verify_frontend_fixture_server.sh
bash scripts/verify_frontend_fixture_server.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-fixture-server-foundation
rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S
```
