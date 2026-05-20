# Task Contract

## Task

- 이름: codex-oauth-llm-provider
- 요청: OpenAI API key 없이 Codex ChatGPT OAuth login을 이용하는 LLM provider boundary를 추가한다.
- 담당: Codex
- 날짜: 2026-05-17

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `event-intelligence-llm-extract`가 `provider=codex_oauth`로 Codex CLI를 read-only/ephemeral subprocess boundary에서 호출할 수 있고, OAuth token 파일을 직접 읽거나 복사하지 않으며, DB에 AI invocation/artifact/event 결과를 저장하는 smoke가 통과한다.

## Why

- 사용자는 무료/기존 ChatGPT subscription 기반 인증을 요구했다.
- 공개 프로젝트들은 Codex OAuth provider를 활용하지만, 공식 OpenAI API key 인증과 같은 경계로 취급하면 안 된다.
- 안전한 구현은 token 추출이 아니라 `codex exec`를 별도 local runtime으로 호출하고 structured output만 수집하는 방식이다.

## Scope

- 포함:
  - `codex_oauth` provider adapter
  - Codex CLI command boundary validation
  - event intelligence extraction CLI의 fixture/codex provider 분기
  - repo-outside runtime env의 `STOCKANALYSIS_LLM_PROVIDER=codex_oauth`
  - 실제 local Codex OAuth smoke
  - task docs/handoff/review
- 제외:
  - `~/.codex/auth.json` 읽기, 복사, 파싱
  - ChatGPT/Codex OAuth token을 `api.openai.com` Bearer token처럼 직접 사용
  - FastAPI request path에서 LLM 호출
  - 추천/매수/매도 판단 자동화
  - paper trading 또는 real trading

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/sec/ai_event_extract.py`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/operations/env_readiness.py`
  - `tests/test_sec_ai_event_extract.py`
  - `tests/test_data_operations_env_readiness.py`
  - repo-outside `/private/tmp/stockanalysis-runtime/data-operations.real.env`
  - root `.env` keys only, still git-ignored
  - task docs
- 수정 금지 파일:
  - `~/.codex/auth.json`
  - production secrets
  - DB migrations
  - broker/order flow

## Verification Commands

- 검증에 사용할 명령:
  - `codex login status`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m stockanalysis.operations.cli env-readiness --env-file /private/tmp/stockanalysis-runtime/data-operations.real.env`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_sec_ai_event_extract tests.test_data_operations_env_readiness tests.test_ingest_cli -v`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m stockanalysis.ingest.cli event-intelligence-llm-extract --external-document-id 0000320193-24-000123 --provider codex_oauth --model-name codex-cli-default --reasoning-effort low --max-input-chars 1800 --min-confidence 0.5`
  - `bash scripts/verify_project_execution_roadmap.sh`

## Completion Criteria

- [ ] `codex_oauth` readiness passes without `OPENAI_API_KEY`.
- [ ] unit tests prove the adapter does not reference `auth.json`.
- [ ] real Codex OAuth smoke persists `ai.model_invocation`, `ai.extraction_artifact`, and canonical event rows.
- [ ] task handoff records remaining caveats.

## Risks

- Codex CLI behavior can change independently of the OpenAI API.
- Structured output schema must stay strict enough for DB persistence but simple enough for Codex CLI output schema validation.
- OAuth provider is appropriate for local data operations jobs, not synchronous FastAPI request handling.
