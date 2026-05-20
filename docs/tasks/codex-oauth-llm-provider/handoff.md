# Session Handoff

## Active Task

- 이름: codex-oauth-llm-provider
- 담당: Codex
- 날짜: 2026-05-17

## Current Status

- 완료:
  - `event-intelligence-llm-extract` now supports `provider=codex_oauth`.
  - Fixture provider remains supported.
  - `--llm-output-json` is only required for fixture mode.
  - Codex provider calls `codex exec` through a subprocess with `read-only`, `never`, `ephemeral`, `ignore-user-config`, and `ignore-rules`.
  - The provider writes a temporary strict output schema and parses the final JSON output.
  - `STOCKANALYSIS_LLM_PROVIDER=codex_oauth`, `STOCKANALYSIS_CODEX_CLI_COMMAND=codex`, and `STOCKANALYSIS_CODEX_TIMEOUT_SECONDS=300` were set in repo-ignored/root and repo-outside runtime envs.
  - Runtime env readiness passes without `OPENAI_API_KEY`.
  - `codex login status` reports `Logged in using ChatGPT`.
  - Real Codex OAuth smoke succeeded for SEC document `0000320193-24-000123`.
- 진행 중:
  - none.
- 막힌 점:
  - Codex CLI still emits local skill/plugin warnings from the user's Codex installation, but the smoke succeeds.
  - This is a local data operations provider boundary, not a production OpenAI API integration.

## Verification

- Passed:
  - `codex login status`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m stockanalysis.operations.cli env-readiness --env-file /private/tmp/stockanalysis-runtime/data-operations.real.env`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_sec_ai_event_extract tests.test_data_operations_env_readiness tests.test_ingest_cli -v`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall src/stockanalysis/ingest/sec/ai_event_extract.py src/stockanalysis/operations/env_readiness.py tests/test_sec_ai_event_extract.py tests/test_data_operations_env_readiness.py`
  - real smoke: `event-intelligence-llm-extract --provider codex_oauth ...`
  - DB check: `codex_oauth_invocations=1`, `event_intelligence_runs=1`, `codex_oauth_events=2`

## Exact Next Step

- exact next step: build a data-operations runner wrapper for scheduled/offline `codex_oauth` extraction batches with per-job artifact capture and retry policy, still keeping LLM calls out of FastAPI request paths.

## Risks

- Codex CLI is a local tool/runtime dependency and can change separately from this repository.
- Existing Codex global skill/plugin warnings should be cleaned up outside this repo if they become noisy or start failing future smoke runs.
- `codex_oauth` should remain local/offline job-only until production authentication and quota behavior are explicitly documented.
