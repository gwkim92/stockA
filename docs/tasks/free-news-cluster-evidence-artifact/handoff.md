# Session Handoff

## Active Task

- 이름: free-news-cluster-evidence-artifact
- 담당: Codex
- 날짜: 2026-05-19

## Current Status

- 완료:
  - task contract created.
  - `news-rss-cluster-evidence-run` operations CLI added.
  - Local deterministic cluster summaries are written as `ai.extraction_artifact.artifact_type = 'news_cluster_summary'`.
  - `ai.model_invocation` records provider `local_rules`, model `news_cluster_summary_v1`, 0 input tokens, and 0 estimated cost.
  - Real local DB run inserted 4 artifacts for run_id `95`: AI 반도체 사이클, 금리·연준, 미국 시장 폭, 에너지·지정학.
  - Existing API now exposes representative event evidence ids, for example `event-20 -> ai-evidence-2`.
- 진행 중:
  - none.
- 막힌 점:
  - none.

## Exact Next Step

- 다음 세션은 이것부터 시작: show these saved `news_cluster_summary` artifacts more explicitly on the frontend AI evidence page, then decide whether to build a proper RAG/ontology store.

## Verification

- Passed:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_news_rss_cluster_evidence tests.test_data_operations_cli`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall src/stockanalysis/ingest/news src/stockanalysis/operations/cli.py tests/test_news_rss_cluster_evidence.py`
  - real DB dry-run: `news-rss-cluster-evidence-run --as-of-date 2026-05-19 --event-limit 100 --max-clusters 4 --dry-run` planned 4 clusters from 40 events.
  - real DB run: `news-rss-cluster-evidence-run --as-of-date 2026-05-19 --event-limit 100 --max-clusters 4` inserted 4 artifacts, failed 0.
  - Authenticated FastAPI `/api/events?asOfDate=2026-05-19&eventType=all&limit=8` shows `ai_extracted_count: 6` and representative RSS events with `ai-evidence-2`, `ai-evidence-3`, `ai-evidence-4`.
  - Authenticated FastAPI `/api/ai-evidence/ai-evidence-2` shows `evidence_type: news_cluster_summary`, `provider: local_rules`, `model_id: news_cluster_summary_v1`, `input_tokens: 0`, `estimated_cost_usd: 0.0`.
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task free-news-cluster-evidence-artifact`
  - `git diff --check`

## Risks

- This creates audit evidence from deterministic local rules only. It is not final LLM reasoning, RAG retrieval, ontology persistence, or recommendation quality.
- Current cluster precision inherits the free RSS enrichment rules. For example broad energy/geopolitics headlines can still carry market proxy symbols; precision tuning should precede production-quality signals.
