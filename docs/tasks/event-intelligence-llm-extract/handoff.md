# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: event-intelligence-llm-extract
- 담당: Codex
- 날짜: 2026-04-23

## Current Status

- 완료:
  - fixture provider 기반 `event-intelligence-llm-extract` runner를 추가했다.
  - AI audit tables와 canonical event write path를 연결했다.
  - CLI, unit tests, Docker verify, 운영 문서를 추가했다.
  - 이전 deterministic pipeline이 계속 기반이라는 점을 task 문서에 남겼다.
- 막힌 점:
  - 아직 없음.

## Files Touched

- 생성:
  - `docs/plans/2026-04-23-event-intelligence-llm-extract.md`
  - `docs/event-intelligence-llm-extract.md`
  - `docs/tasks/event-intelligence-llm-extract/contract.md`
  - `docs/tasks/event-intelligence-llm-extract/plan.md`
  - `docs/tasks/event-intelligence-llm-extract/handoff.md`
  - `docs/tasks/event-intelligence-llm-extract/review.md`
  - `scripts/verify_event_intelligence_llm_extract.sh`
  - `src/stockanalysis/ingest/sec/ai_event_extract.py`
  - `tests/test_sec_ai_event_extract.py`
  - `tests/fixtures/llm_sec_event_aapl_10k_structured.json`
- 수정:
  - `README.md`
  - `docs/ai-intelligence-architecture.md`
  - `docs/verification-plan.md`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_ingest_cli.py`
- 의도적으로 안 건드린 것:
  - existing heuristic SEC event extraction code path
  - market universe bootstrap
  - market price universe backfill
  - strategy universe slicing
  - recommendation scoring
  - provider credentials and live network calls

## Decisions

- 결정:
  - live OpenAI 호출은 이번 task에서 제외하고 fixture provider로 provider boundary와 DB write path를 먼저 검증한다.
  - 기존 heuristic SEC event extraction은 그대로 둔다.
  - AI output은 바로 recommendation으로 가지 않고 `ai.extraction_artifact`와 canonical `event.*`에만 반영한다.
  - 이전 작업인 데이터 수집기, market universe, price backfill, strategy universe slicing은 계속 다음 recommendation pipeline의 기반으로 유지한다.
- 이유:
  - API key, retry, rate-limit, provider pricing을 건드리기 전에 deterministic 검증 가능한 AI audit path가 먼저 필요하다.

## Verification Already Run

- 명령: `python3 -m compileall src tests`
- 관찰한 결과: 성공

- 명령: `PYTHONPATH=src python3 -m unittest tests.test_sec_ai_event_extract tests.test_ingest_cli -v`
- 관찰한 결과: 새 AI extraction unit/CLI tests 포함 26개 테스트 통과

- 명령: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- 관찰한 결과: 전체 106개 테스트 통과

- 명령: `bash -n scripts/verify_event_intelligence_llm_extract.sh`
- 관찰한 결과: 성공

- 명령: `bash scripts/verify_event_intelligence_llm_extract.sh`
- 관찰한 결과: sandbox 내부 Docker socket permission denied로 실패했고, 같은 명령을 승인된 권한 상승으로 다시 실행해 성공했다. Docker Postgres에서 canonical event 1건, `ai.model_invocation` 1건, `ai.document_chunk` 1건, `ai.extraction_artifact` 1건, `ai.prompt_template` 1건, latest `event_intelligence_llm_extract` run status `succeeded`를 확인했다.

## Still Unverified

- 항목: Docker Postgres에서 AI event extraction end-to-end
- 왜 중요한가: unit test만으로는 `ai.*` tables와 canonical `event.*` tables가 함께 쓰이는지 증명할 수 없다.
- 항목: live OpenAI Responses API call
- 왜 중요한가: 이번 task는 fixture provider까지만 구현했으므로 실제 provider auth, retry, rate limit, network failure는 아직 검증하지 않았다.

## Exact Next Step

- 다음 세션은 이것부터 시작: live OpenAI Responses API adapter와 `market-feature-snapshot`을 병렬 backlog로 유지한다. AI 쪽은 provider adapter와 eval/rate-limit policy가 필요하고, deterministic 쪽은 recommendation 이전 feature snapshot이 필요하다.

## Risks

- 위험:
  - fixture provider는 live LLM 품질을 검증하지 않는다.
  - OpenAI Responses API payload는 후속 task에서 공식 문서 기준으로 별도 검증해야 한다.
  - AI event는 아직 classification/instrument impact까지 자동 연결하지 않는다.
  - 이전 deterministic market feature chain을 멈추면 recommendation까지 이어지는 경로가 비게 된다.
- 대응:
  - fixture provider로 schema/audit/canonical write path를 먼저 고정한다.
  - live provider는 별도 task에서 credential, retry, rate limit, eval gate와 함께 붙인다.
  - 기존 `event-classification-impact-bootstrap`, `event-instrument-impact-bootstrap`을 후속으로 재사용한다.
  - `market-feature-snapshot`과 cycle/thesis/recommendation task를 계속 이어간다.

## Useful Context

- 파일:
  - `docs/ai-intelligence-architecture.md`
  - `db/migrations/0005_ai_intelligence.sql`
  - `src/stockanalysis/ingest/sec/event_extract.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `scripts/verify_sec_filings_event_extract.sh`
- 다시 찾기 싫은 배경지식:
  - `event.event`는 `dedupe_key` unique index가 있다.
  - `render_sec_event_extract_sql`은 candidate를 canonical event와 document link로 upsert한다.
  - `ai.model_invocation`은 token/cost/latency/status audit 용도다.
