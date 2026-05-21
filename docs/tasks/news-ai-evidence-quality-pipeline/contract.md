# Task Contract

## Task

- 이름: news-ai-evidence-quality-pipeline
- 요청: 뉴스 RSS 분석을 rule-only cluster summary에서 `codex_oauth` AI 후보 추출, Postgres ontology-lite/RAG context, validator, canonical impact 반영 구조로 전환한다.
- 담당: Codex
- 날짜: 2026-05-21

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `stockanalysis-operations news-rss-ai-extract-run --provider codex_oauth --execute`가 RSS 뉴스 후보를 offline batch로 분석하고, `ai.extraction_artifact.artifact_type='news_event_candidate'`에 후보를 저장하며, validator를 통과한 theme/instrument impact만 `event.event_classification_impact`와 `event.event_instrument_impact`에 반영한다.

## Why

- 기존 `news-rss-enrichment-intraday`는 feed/keyword hardcoded rule만 사용한다.
- 기존 `event-intelligence-weekly`는 local-rule cluster summary를 AI evidence처럼 저장하지만, 실제 뉴스 본문/요약의 구조화 판단은 하지 않는다.
- 투자 운영 시스템은 어떤 뉴스가 어떤 테마/종목/방향/근거로 연결됐는지 추적해야 하므로 AI 후보와 deterministic validator를 분리해야 한다.

## Scope

- 포함:
  - news AI extraction runner
  - `codex_oauth` provider boundary
  - fixture provider test path
  - Postgres ontology-lite/RAG context SQL
  - validator-gated canonical impact upsert
  - operations CLI command
  - scheduler/orchestrator command reference update
  - focused tests and verify script
- 제외:
  - paid OpenAI API
  - external vector DB, Neo4j, RDF store
  - recommendation scoring 공식 변경
  - broker/order flow
  - FastAPI request path에서 LLM 호출

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/news/ai_extract.py`
  - `src/stockanalysis/ingest/news/models.py`
  - `src/stockanalysis/ingest/news/sql.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/operations/manual_local_ingest_smoke.py`
  - `src/stockanalysis/operations/local_runtime_status.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `apps/web/src/lib/korean-labels.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - focused tests, fixtures, verify script, task docs
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations
  - recommendation scoring
  - benchmark/evaluation split
  - broker/order submission code
  - external scheduler deployment manifests

## Boundaries

- `codex_oauth`는 offline scheduled/batch job에서만 호출한다.
- AI output은 canonical table에 직접 쓰지 않고 `news_event_candidate` artifact로 먼저 저장한다.
- unknown theme, unknown symbol, invalid direction, low confidence는 canonical impact 반영에서 제외한다.
- rule enrichment는 fallback/baseline으로 유지한다.

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src python3 -m unittest tests.test_news_rss_ai_extract tests.test_data_operations_cli tests.test_operating_data_orchestrator tests.test_manual_local_ingest_smoke`
  - `bash scripts/verify_news_ai_evidence_quality_pipeline.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task news-ai-evidence-quality-pipeline`
  - `git diff --check`

## Done Criteria

- [x] `news-rss-ai-extract-run` CLI exists.
- [x] dry-run does not write DB or call provider.
- [x] fixture provider writes AI invocation, `news_event_candidate` artifact, and validated canonical impacts.
- [x] unknown theme/symbol and low confidence are rejected.
- [x] event-intelligence scheduler/orchestrator references use the new runner.
- [x] focused verification script exists.
