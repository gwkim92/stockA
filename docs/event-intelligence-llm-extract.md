# Event Intelligence LLM Extract

이 문서는 SEC raw filing artifact를 AI-style structured event artifact와 canonical event로 연결하는 첫 런타임 AI 경로를 설명한다.

## Why This Exists

이 프로젝트는 이미 아래 기반을 갖고 있다.

- data collectors
- SEC filing metadata ingest
- SEC raw artifact fetch
- macro ingest
- market universe bootstrap
- market price backfill
- strategy universe slicing

이번 작업은 그 기반 위에 AI를 끼워 넣는 첫 단계다. 기존 deterministic pipeline을 지우는 것이 아니라, 비정형 SEC 문서 이해를 구조화해 `ai.*` audit tables와 canonical `event.*` tables로 남기는 계층을 추가한다.

## Current Scope

이번 구현은 live provider가 아니라 `fixture provider`를 사용한다.

이유:

- API key와 retry/rate-limit 정책 없이도 구조와 provenance를 먼저 검증할 수 있다.
- `ai.model_invocation`, `ai.document_chunk`, `ai.extraction_artifact`, canonical `event.event` write path를 안전하게 고정할 수 있다.
- 기존 heuristic `sec-filings-event-extract`를 그대로 유지할 수 있다.

## CLI

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli event-intelligence-llm-extract \
  --external-document-id 0000320193-24-000123 \
  --llm-output-json tests/fixtures/llm_sec_event_aapl_10k_structured.json \
  --provider fixture \
  --model-name gpt-5.4-nano \
  --reasoning-effort low \
  --max-input-chars 700 \
  --min-confidence 0.9
```

## What It Writes

### AI audit path

- `ai.prompt_template`
- `ai.document_chunk`
- `ai.model_invocation`
- `ai.extraction_artifact`

### Canonical path

- `event.event`
- `event.event_document_link`

## Flow

```text
ingest.source_document + raw_storage_uri
  -> bounded document chunk
  -> fixture provider structured output
  -> ai.model_invocation
  -> ai.extraction_artifact
  -> validated SecExtractedEventCandidate
  -> event.event + event.event_document_link
```

## Boundaries

- AI output confidence가 `min_confidence`보다 낮으면 canonical event write를 거부한다.
- raw full text는 Postgres에 저장하지 않는다.
- document chunk는 preview, hash, token count, metadata만 저장한다.
- recommendation, scoring, portfolio decision은 이번 task 범위가 아니다.

## Verification

- `python3 -m compileall src tests`
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- `bash scripts/verify_event_intelligence_llm_extract.sh`

Docker verify는 아래를 확인한다.

- SEC filing metadata 1건 upsert
- raw filing artifact 1건 attach
- AI event extraction 1건 수행
- canonical event 1건
- AI model invocation 1건
- AI document chunk 1건
- AI extraction artifact 1건
- latest `event_intelligence_llm_extract` pipeline run status `succeeded`

## What Comes Next

두 갈래가 있다.

1. live OpenAI Responses API adapter
2. AI event를 기존 `event-classification-impact-bootstrap`, `event-instrument-impact-bootstrap` 이후 cycle/thesis/recommendation chain으로 연결

이와 별개로 이전 작업 흐름에서 recommendation으로 가려면 `market-feature-snapshot`도 필요하다. 즉 AI path와 deterministic market feature path를 병렬로 계속 가져가야 한다.
