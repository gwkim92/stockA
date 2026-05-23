# Task Contract

## Task

- 이름: news-korean-translation-batch
- 요청: 정확한 문장 단위 한국어 번역을 위해 Codex OAuth 배치가 `korean_title`, `korean_summary`, `translation_confidence`를 DB에 저장하도록 만든다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `stockanalysis-operations news-rss-translation-run --provider codex_oauth --execute`가 RSS 원천 문서를 offline batch로 번역하고, `ingest.source_document.korean_title`, `ingest.source_document.korean_summary`, `ingest.source_document.translation_confidence`를 저장하며, 화면은 저장된 번역값을 heuristic 문구보다 우선 표시한다.

## Scope

- Add DB fields for `korean_title`, `korean_summary`, and `translation_confidence`.
- Add an offline `codex_oauth` batch runner that translates bounded RSS title/summary text and records `ai.model_invocation`.
- Add an operations CLI command and include it in the news intraday profile before cluster/AI evidence surfaces read the documents.
- Expose persisted translation fields through frontend DTOs and make the UI prefer them over heuristic labels.
- Keep FastAPI request handling read-only; do not call LLM from web requests.

## Mutable Surface

- 수정 가능한 파일:
  - `db/migrations/0016_news_document_translation.sql`
  - `src/stockanalysis/ingest/news/translation.py`
  - `src/stockanalysis/ingest/news/sql.py`
  - `src/stockanalysis/ingest/news/models.py`
  - `src/stockanalysis/ingest/news/cluster_evidence.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/components/news-title-block.tsx`
  - affected frontend pages/types
  - focused tests and task docs
- 수정 금지 파일:
  - `.env` secret values
  - broker/order submission code
  - recommendation scoring formulas
  - external paid translation/RAG provider configuration

## Out Of Scope

- Paid translation APIs.
- External vector DB, Neo4j, RDF, or other hosted ontology services.
- Buy/sell/order decisions.
- Editing unrelated dogfood output or secrets.

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_translation tests.test_data_operations_cli tests.test_operating_data_orchestrator tests.test_data_operations_cadence tests.test_frontend_live_adapter tests.test_news_rss_cluster_evidence tests.test_news_rss_ai_extract`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m awh verify --repo . --task news-korean-translation-batch`
  - `git diff --check`
