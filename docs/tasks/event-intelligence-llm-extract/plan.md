# Task Plan

## 1. Keep Existing Pipeline Intact

- 기존 `sec-filings-event-extract` heuristic 경로는 수정하지 않는다.
- 새 AI 경로는 `event-intelligence-llm-extract` CLI로 추가한다.
- 이전 작업인 data collectors, SEC raw fetch, market universe, price backfill, strategy universe slicing은 이후 feature/recommendation 단계의 기반으로 계속 유지한다.

## 2. Implement Runner

- `src/stockanalysis/ingest/sec/ai_event_extract.py`를 만든다.
- source document lookup은 기존 `load_sec_event_source_document_record`를 재사용한다.
- raw artifact body를 text로 변환하고 max input char로 제한한 chunk를 만든다.
- prompt template과 document chunk를 `ai` schema에 upsert한다.
- fixture provider output을 validation하고 token/cost metadata를 읽는다.
- model invocation과 extraction artifact를 저장한다.
- validated event candidate를 canonical `event.event`와 `event.event_document_link`로 upsert한다.

## 3. Add CLI

- `event-intelligence-llm-extract` command를 추가한다.
- required: `--external-document-id`
- fixture mode required: `--llm-output-json`
- options: `--provider`, `--model-name`, `--reasoning-effort`, `--max-input-chars`, `--min-confidence`

## 4. Add Tests

- fixture response parse test
- confidence validation test
- SQL rendering test
- runner happy path test
- runner failure status test
- CLI summary test

## 5. Add Docker Verify

- Run migrations/seeds.
- Run SEC filing metadata upsert.
- Run SEC raw fetch.
- Run `event-intelligence-llm-extract`.
- Assert canonical event, model invocation, document chunk, extraction artifact, run status.

## 6. Update Docs And Handoff

- Add `docs/event-intelligence-llm-extract.md`.
- Link README and verification plan.
- Update `docs/ai-intelligence-architecture.md` immediate next implementation section.
- Update task handoff/review with actual verification output.
