# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: ai-intelligence-architecture
- 요청: 2026-04-23 기준 최신 AI 기술, 토큰 절감, 데이터 관리, RAG, 온톨로지, 품질 검증을 고려해 프로젝트의 AI 도입 설계를 공식화한다.
- 담당: Codex
- 날짜: 2026-04-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 프로젝트는 AI가 어디에 들어가고 어디에 들어가면 안 되는지, RAG와 ontology를 어떻게 병행할지, 토큰/비용/품질을 어떻게 관리할지 문서와 DB boundary로 설명할 수 있다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: 투자 시스템에서 AI를 추천 결정자로 직접 넣으면 재현성과 감사 가능성이 깨진다. AI는 비정형 데이터를 구조화하고 투자 thesis/review/report를 보조하되, canonical state와 recommendation scoring은 검증 가능한 코드가 소유해야 한다.

## Inputs

- 관련 코드:
  - `db/migrations/`
  - `scripts/verify_strategy_universe_slicing.sh`
- 관련 문서:
  - `docs/ai-role-map.md`
  - `docs/db-schema-design.md`
  - `docs/verification-plan.md`
  - `docs/strategy-universe-slicing.md`
- 외부 근거:
  - OpenAI official docs for models, Responses API, prompt caching, retrieval, structured outputs, function calling, Batch API, Evals, embeddings
  - Microsoft GraphRAG docs
  - GraphRAG arXiv paper
  - W3C RDF/OWL/SHACL specifications
- 이전 결정:
  - AI는 추천 결정자가 아니라 intelligence/report layer다.
  - 첫 AI 런타임 진입점은 `event-intelligence-llm-extract`가 적절하다.
  - deterministic ingestion, universe slicing, scoring은 AI가 소유하지 않는다.

## Scope

- 포함:
  - AI intelligence architecture 문서
  - RAG vs ontology 결론
  - token/cost governance
  - quality gates and eval strategy
  - AI metadata/audit DB schema
  - Docker verification script
  - README, verification plan, DB schema design 업데이트
- 제외:
  - live LLM API call 구현
  - provider credential handling
  - production vector DB 도입
  - full RDF triple store 도입
  - trading automation
  - recommendation scoring 변경

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `db/migrations/0005_ai_intelligence.sql`
  - `docs/ai-intelligence-architecture.md`
  - `docs/ai-role-map.md`
  - `docs/db-schema-design.md`
  - `docs/plans/2026-04-23-ai-intelligence-architecture.md`
  - `docs/tasks/ai-intelligence-architecture/`
  - `docs/verification-plan.md`
  - `scripts/verify_ai_intelligence_architecture.sh`
- 수정 금지 파일:
  - existing ingest runners
  - existing strategy universe runner
  - tests for unrelated ingest behavior, unless needed for verification wiring
  - API keys or deployment config
- 검증에 사용할 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n scripts/verify_ai_intelligence_architecture.sh`
  - `bash scripts/verify_ai_intelligence_architecture.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task ai-intelligence-architecture`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - `docs/ai-intelligence-architecture.md`
  - `db/migrations/0005_ai_intelligence.sql`
  - `scripts/verify_ai_intelligence_architecture.sh`
  - `docs/tasks/ai-intelligence-architecture/contract.md`
  - `docs/tasks/ai-intelligence-architecture/plan.md`
  - `docs/tasks/ai-intelligence-architecture/handoff.md`
  - `docs/tasks/ai-intelligence-architecture/review.md`
  - `docs/plans/2026-04-23-ai-intelligence-architecture.md`
- 선택 결과물:
  - `docs/ai-role-map.md` 보강
  - `docs/db-schema-design.md` 보강
  - `README.md` 링크 보강

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] AI가 추천 결정자가 아니라 intelligence layer임이 명확하다
- [x] RAG와 ontology 병행 전략이 명확하다
- [x] token/cost/quality governance가 문서화되어 있다
- [x] AI metadata schema가 실제 Postgres에 적용된다

## Verification Plan

- 자동 검증: compileall, unittest, shell syntax, Docker migration/insert verify, harness verify, placeholder 검색
- 수동 검증: `docs/ai-intelligence-architecture.md`가 최신 AI 기술을 무비판 도입하지 않고 프로젝트의 재현성/감사성 원칙에 맞게 제한하는지 확인
- 브라우저, 로그, metric 검증: 현재는 설계/DB boundary 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: AI schema tables와 샘플 metadata rows가 Docker Postgres에 생성되고, task handoff/review가 검증 결과를 포함한다

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `db/migrations/0005_ai_intelligence.sql`, AI architecture docs, verify script만 제거하면 이전 deterministic ingest/market/signal pipeline 상태로 돌아간다.

## Open Questions

- 질문: 실제 provider는 OpenAI 단일로 시작할지, model gateway를 처음부터 multi-provider로 열지
- 답이 없을 때 적용할 임시 가정: OpenAI-compatible adapter 하나로 시작하되 provider/model fields와 adapter boundary는 multi-provider를 막지 않게 둔다.

- 질문: vector store는 OpenAI vector store, pgvector, 외부 vector DB 중 무엇으로 시작할지
- 답이 없을 때 적용할 임시 가정: Postgres에는 vector metadata만 저장하고 실제 vector backend는 adapter URI로 늦게 결정한다.
