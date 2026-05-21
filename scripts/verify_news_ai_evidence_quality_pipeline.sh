#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"

bash -n scripts/verify_news_ai_evidence_quality_pipeline.sh

PYTHONPATH=src "$PYTHON_BIN" -m compileall \
  src/stockanalysis/ingest/news/ai_extract.py \
  src/stockanalysis/ingest/news/sql.py \
  src/stockanalysis/operations/cli.py \
  tests/test_news_rss_ai_extract.py >/dev/null

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_news_rss_ai_extract \
  tests.test_data_operations_cli.DataOperationsCliTests.test_news_rss_ai_extract_run_command_passes_env_and_provider_limits \
  tests.test_data_operations_cli.DataOperationsCliTests.test_news_rss_ai_extract_run_does_not_fail_exit_on_candidate_fallback \
  tests.test_operating_data_orchestrator.OperatingDataOrchestratorTests.test_news_intraday_profile_does_not_require_portfolio_positions \
  tests.test_manual_local_ingest_smoke.ManualLocalIngestSmokeTests.test_event_intelligence_job_uses_news_ai_extract_runner

grep -q "news-rss-ai-extract-run" src/stockanalysis/operations/cli.py
grep -q "news_event_candidate" src/stockanalysis/ingest/news/ai_extract.py
grep -q "codex_oauth" src/stockanalysis/ingest/news/ai_extract.py
grep -q "ref.classification_edge" src/stockanalysis/ingest/news/sql.py
grep -q "news-ai-evidence-quality-pipeline" docs/tasks/news-ai-evidence-quality-pipeline/contract.md
