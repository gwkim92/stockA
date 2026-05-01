# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: ai-intelligence-architecture
- 담당: Codex
- 날짜: 2026-04-23

## Current Status

- 완료:
  - 최신 AI/RAG/ontology 근거를 확인하고 프로젝트 설계 문서에 반영했다.
  - AI intelligence architecture 문서를 추가했다.
  - AI metadata/audit schema migration을 추가했다.
  - Docker Postgres 검증 스크립트를 추가했다.
  - README, AI role map, DB schema design, verification plan을 연결했다.
- 막힌 점:
  - 아직 없음.

## Files Touched

- 생성:
  - `docs/plans/2026-04-23-ai-intelligence-architecture.md`
  - `docs/ai-intelligence-architecture.md`
  - `docs/tasks/ai-intelligence-architecture/contract.md`
  - `docs/tasks/ai-intelligence-architecture/plan.md`
  - `docs/tasks/ai-intelligence-architecture/handoff.md`
  - `docs/tasks/ai-intelligence-architecture/review.md`
  - `db/migrations/0005_ai_intelligence.sql`
  - `scripts/verify_ai_intelligence_architecture.sh`
- 수정:
  - `README.md`
  - `docs/ai-role-map.md`
  - `docs/db-schema-design.md`
  - `docs/verification-plan.md`
- 의도적으로 안 건드린 것:
  - existing ingest runners
  - existing strategy universe runner
  - recommendation scoring
  - provider credentials
  - deployment config

## Decisions

- 결정:
  - AI는 추천 결정자가 아니라 intelligence/report layer다.
  - 초기 AI 런타임 진입점은 `event-intelligence-llm-extract`다.
  - RAG와 ontology/knowledge graph를 병행한다.
  - 초기 graph/ontology는 Postgres tables와 adapter metadata로 시작한다.
  - model gateway를 둬 provider/model/reasoning effort를 task별로 라우팅한다.
  - token/cost는 `ai.model_invocation`에서 추적한다.
- 이유:
  - 중장기 투자 시스템은 최신 AI 성능보다 재현성, evidence, audit, eval이 먼저 필요하기 때문이다.

## Verification Already Run

- 명령: `python3 -m compileall src tests`
- 관찰한 결과: 성공

- 명령: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- 관찰한 결과: 99개 테스트 통과

- 명령: `bash -n scripts/verify_ai_intelligence_architecture.sh`
- 관찰한 결과: 성공

- 명령: `bash scripts/verify_ai_intelligence_architecture.sh`
- 관찰한 결과: 성공. Docker Postgres에서 migration/seed 적용 후 `ai` schema tables 6개 존재, 샘플 `ai.prompt_template`, `ai.model_invocation`, `ai.document_chunk`, `ai.embedding_index`, `ai.extraction_artifact`, `ai.eval_run` row insert를 확인했다.

- 명령: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task ai-intelligence-architecture`
- 관찰한 결과: `Task ai-intelligence-architecture passed readiness checks.`

- 명령: `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`
- 관찰한 결과: 출력 없음. exit code 1은 ripgrep이 match를 찾지 못한 정상 상태다.

## Still Unverified

- 항목: live LLM provider call
- 왜 중요한가: 이번 작업은 architecture와 DB boundary까지이며 실제 OpenAI API 호출, credential, rate limit, retry는 아직 구현하지 않았다.

- 항목: real vector retrieval quality
- 왜 중요한가: 현재는 vector storage URI metadata만 검증했고, 실제 vector backend와 retrieval 품질은 후속 task에서 검증해야 한다.

- 항목: GraphRAG corpus quality
- 왜 중요한가: GraphRAG는 비용이 큰 indexing 단계가 있어 sector/theme pilot이 필요하다.

## Exact Next Step

- 다음 세션은 이것부터 시작: `event-intelligence-llm-extract` task를 만들고 model gateway, prompt template, structured extraction artifact 저장 경로를 구현한다.

## Risks

- 위험:
  - 최신 모델명/가격은 provider 문서가 바뀌면 달라질 수 있다.
  - GraphRAG는 indexing 비용이 크므로 전체 corpus에 즉시 적용하면 비용이 커질 수 있다.
  - ontology를 너무 빨리 정교화하면 구현 속도가 떨어진다.
- 대응:
  - 모델명은 config/gateway에서 관리한다.
  - GraphRAG는 sector/theme pilot부터 시작한다.
  - 초기 ontology는 Postgres graph tables와 relation type으로 제한한다.

## Useful Context

- 파일:
  - `docs/ai-role-map.md`
  - `docs/db-schema-design.md`
  - `db/migrations/0005_ai_intelligence.sql`
  - `scripts/verify_ai_intelligence_architecture.sh`
- 다시 찾기 싫은 배경지식:
  - OpenAI 공식 문서는 2026-04-23 기준 `gpt-5.4`를 복잡한 reasoning/coding 기준 모델로, `gpt-5.4-mini/nano`를 비용/지연 최적화 모델로 제시한다.
  - Prompt caching은 static prefix, tool schema, structured output schema를 앞에 둬야 효과가 난다.
  - Batch API는 historical extraction, embedding backfill, eval run에 맞다.
