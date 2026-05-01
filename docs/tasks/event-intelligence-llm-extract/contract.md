# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: event-intelligence-llm-extract
- 요청: `ai-intelligence-architecture`에서 정한 첫 AI 런타임 진입점으로 SEC raw filing artifact를 structured AI event artifact와 canonical event로 변환하는 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `event-intelligence-llm-extract` CLI가 SEC source document, raw artifact, structured output fixture를 읽어 `ai.model_invocation`, `ai.document_chunk`, `ai.extraction_artifact`, `event.event`, `event.event_document_link`에 감사 가능한 결과를 저장한다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: AI를 추천 결정에 직접 넣기 전에 문서 이해와 이벤트 구조화 계층부터 검증해야 한다. SEC filing은 이미 수집기, raw artifact, heuristic event 경로가 있으므로 AI extraction을 붙이기 가장 안전한 첫 지점이다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/ingest/sec/event_extract.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `src/stockanalysis/ingest/cli.py`
  - `db/migrations/0005_ai_intelligence.sql`
- 관련 문서:
  - `docs/ai-intelligence-architecture.md`
  - `docs/ai-role-map.md`
  - `docs/sec-filings-event-extraction.md`
  - `docs/verification-plan.md`
- 이전 결정:
  - AI는 추천 결정자가 아니라 intelligence/report layer다.
  - `event-intelligence-llm-extract`가 첫 AI 런타임 진입점이다.
  - RAG와 ontology는 병행하지만, 이번 task는 bounded SEC raw artifact chunk와 AI audit metadata에 집중한다.

## Scope

- 포함:
  - fixture provider 기반 structured event extraction
  - prompt template upsert
  - document chunk metadata upsert
  - model invocation audit insert
  - extraction artifact insert
  - canonical event upsert
  - CLI, unit tests, Docker verification, docs
- 제외:
  - live OpenAI API call
  - API key/secret handling
  - production vector store
  - GraphRAG indexing
  - recommendation score 변경
  - portfolio action 생성

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/ai-intelligence-architecture.md`
  - `docs/event-intelligence-llm-extract.md`
  - `docs/plans/2026-04-23-event-intelligence-llm-extract.md`
  - `docs/tasks/event-intelligence-llm-extract/`
  - `docs/verification-plan.md`
  - `scripts/verify_event_intelligence_llm_extract.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/sec/ai_event_extract.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_sec_ai_event_extract.py`
  - `tests/fixtures/llm_sec_event_aapl_10k_structured.json`
- 수정 금지 파일:
  - existing heuristic SEC event extraction behavior
  - market universe and strategy universe logic
  - recommendation scoring
  - provider credentials or deployment config
- 검증에 사용할 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n scripts/verify_event_intelligence_llm_extract.sh`
  - `bash scripts/verify_event_intelligence_llm_extract.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task event-intelligence-llm-extract`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - `src/stockanalysis/ingest/sec/ai_event_extract.py`
  - `tests/test_sec_ai_event_extract.py`
  - `tests/fixtures/llm_sec_event_aapl_10k_structured.json`
  - `scripts/verify_event_intelligence_llm_extract.sh`
  - `docs/event-intelligence-llm-extract.md`
  - `docs/tasks/event-intelligence-llm-extract/contract.md`
  - `docs/tasks/event-intelligence-llm-extract/plan.md`
  - `docs/tasks/event-intelligence-llm-extract/handoff.md`
  - `docs/tasks/event-intelligence-llm-extract/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] 기존 heuristic event extraction이 유지된다
- [x] AI extraction 결과가 `ai.*` audit tables에 저장된다
- [x] 검증된 AI event candidate만 canonical `event.*` tables에 반영된다
- [x] 이전 데이터 수집기/market universe/strategy universe 작업 흐름을 잊지 않고 다음 단계에 남긴다

## Verification Plan

- 자동 검증: compileall, unittest, shell syntax, Docker integration verify, harness verify, placeholder search
- 수동 검증: `docs/event-intelligence-llm-extract.md`에서 fixture provider와 live provider의 경계가 명확한지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: Docker Postgres에서 AI metadata rows와 canonical SEC event row가 생성되고 latest `event_intelligence_llm_extract` run status가 `succeeded`다.

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: 새 CLI command, `ai_event_extract.py`, verify script, docs만 제거하면 기존 heuristic SEC event pipeline으로 돌아간다.

## Open Questions

- 질문: live provider는 OpenAI Responses API를 바로 붙일지, retry/rate-limit policy task를 먼저 만들지
- 답이 없을 때 적용할 임시 가정: 이번 task는 fixture provider까지 완료하고, live provider는 별도 `openai-responses-provider` task로 진행한다.
