#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$ROOT_DIR"

bash -n scripts/verify_news_rss_raw_body_chunk_index.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/ingest/news/raw_body_chunk_index.py \
  src/stockanalysis/ingest/cli.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_news_rss_raw_body_chunk_index \
  tests.test_ingest_cli.IngestCliTests.test_news_rss_raw_body_chunk_index_cli_prints_summary \
  -v

test -f docs/plans/2026-05-19-news-rss-raw-body-chunk-index.md
test -f docs/tasks/news-rss-raw-body-chunk-index/contract.md
test -f docs/tasks/news-rss-raw-body-chunk-index/handoff.md
test -f docs/tasks/news-rss-raw-body-chunk-index/review.md

grep -q "render_news_rss_raw_body_chunk_candidate_lookup_sql" src/stockanalysis/ingest/news/raw_body_chunk_index.py
grep -q "d.raw_storage_uri is not null" src/stockanalysis/ingest/news/raw_body_chunk_index.py
grep -q "HTMLParser" src/stockanalysis/ingest/news/raw_body_chunk_index.py
grep -q "raw_storage_uri must be under artifact_root" src/stockanalysis/ingest/news/raw_body_chunk_index.py
grep -q "insert into ai.document_chunk" src/stockanalysis/ingest/news/raw_body_chunk_index.py
grep -q "insert into ai.embedding_index" src/stockanalysis/ingest/news/raw_body_chunk_index.py
grep -q "local://stockanalysis/news-rss/raw-body/document/" src/stockanalysis/ingest/news/raw_body_chunk_index.py
grep -q "external_embedding_api.*False" src/stockanalysis/ingest/news/raw_body_chunk_index.py
grep -q "live_llm_call.*False" src/stockanalysis/ingest/news/raw_body_chunk_index.py
grep -q "news-rss-raw-body-chunk-index" src/stockanalysis/ingest/cli.py
grep -q "verify_news_rss_raw_body_chunk_index.sh" docs/verification-plan.md

echo "news RSS raw body chunk index verification passed"
