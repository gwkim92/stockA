# Session Handoff

## Active Task

- 이름: internal-rag-retrieval-foundation-v1
- 담당: Codex
- 날짜: 2026-05-27

## Current Status

- 완료:
  - task contract created.
  - `stockanalysis.ai.internal_rag` context package builder added.
  - `/api/ai/evidence-neighborhoods/{symbol}` now includes `internal_rag_context`.
  - `stockanalysis-operations internal-rag-context-run` added as a read-only context preview command.
  - stock detail page shows internal AI reference material readiness.
  - local Python, frontend, AWH, and verification-script checks passed.
- 진행 중:
  - EC2 deploy and smoke.
- 막힌 점:
  - none.

## Exact Next Step

- exact next step: Run targeted backend/frontend verification, deploy to EC2, and smoke `/api/ai/evidence-neighborhoods/NVDA` plus `/stocks/NVDA`.

## Verification

- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_internal_rag tests.test_frontend_live_adapter tests.test_data_operations_cli`
- passed: `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_internal_rag_retrieval_foundation_v1.sh`
- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task internal-rag-retrieval-foundation-v1`
- passed: `git diff --check`

## Risks

- This is a deterministic context packaging layer, not semantic vector retrieval.
- `pgvector` and external GraphRAG services remain deferred until retrieval quality gaps are measured.
- The context package is read-only and must not change recommendation weights, positions, benchmark, or order flow.
