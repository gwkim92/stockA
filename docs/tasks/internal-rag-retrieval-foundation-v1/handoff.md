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
  - EC2 commit `bfa11d2` deployed and smoke verified.
- 진행 중:
  - none.
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

## EC2 Verification

- deployed commit: `bfa11d2`.
- `stockanalysis-frontend-api.service`: active.
- `stockanalysis-web.service`: active.
- EC2 targeted Python smoke passed for `tests.test_internal_rag`, evidence neighborhood API contract test, and internal RAG CLI tests.
- EC2 Next production build passed.
- CLI smoke wrote `/opt/stockanalysis/artifacts/internal-rag/nvda-context.json`.
- `/api/ai/evidence-neighborhoods/NVDA?asOfDate=2026-05-27&maxItems=12`: `internal_rag_context.status=ready`, `event_count=12`, `evidence_chunk_count=12`, `translated_event_count=12`, all 5 quality gates passed.
- API smoke confirmed `live_llm_call_enabled=false`, `write_enabled=false`, no `vector_storage_uri`, and no read-token env name in response body.
- `/stocks/NVDA`: HTTP 200 and rendered `AI가 이 종목을 다시 분석할 때 참고하는 자료` plus `외부 유료 RAG`.

## Risks

- This is a deterministic context packaging layer, not semantic vector retrieval.
- `pgvector` and external GraphRAG services remain deferred until retrieval quality gaps are measured.
- The context package is read-only and must not change recommendation weights, positions, benchmark, or order flow.
