#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$ROOT_DIR"

bash -n scripts/verify_news_rss_local_chunk_index.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/ingest/news/chunk_index.py \
  src/stockanalysis/ingest/cli.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_news_rss_chunk_index \
  tests.test_ingest_cli.IngestCliTests.test_news_rss_local_chunk_index_cli_prints_summary \
  -v

test -f docs/tasks/news-rss-local-chunk-index/contract.md
test -f docs/tasks/news-rss-local-chunk-index/handoff.md
test -f docs/tasks/news-rss-local-chunk-index/review.md

grep -q "render_news_rss_local_chunk_index_sql" src/stockanalysis/ingest/news/chunk_index.py
grep -q "insert into ai.document_chunk" src/stockanalysis/ingest/news/chunk_index.py
grep -q "insert into ai.embedding_index" src/stockanalysis/ingest/news/chunk_index.py
grep -q "local://stockanalysis/news-rss/document/" src/stockanalysis/ingest/news/chunk_index.py
grep -q "external_embedding_api.*False" src/stockanalysis/ingest/news/chunk_index.py
grep -q "live_llm_call.*False" src/stockanalysis/ingest/news/chunk_index.py
grep -q "news-rss-local-chunk-index" src/stockanalysis/ingest/cli.py
grep -q "verify_news_rss_local_chunk_index.sh" docs/verification-plan.md

echo "news RSS local chunk index verification passed"
