#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$ROOT_DIR"

bash -n scripts/verify_news_rss_raw_body_fetch.sh
"$PYTHON_BIN" -m py_compile \
  src/stockanalysis/ingest/news/raw_fetch.py \
  src/stockanalysis/ingest/cli.py

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_news_rss_raw_fetch \
  tests.test_ingest_cli.IngestCliTests.test_news_rss_raw_fetch_cli_prints_summary \
  -v

test -f docs/plans/2026-05-19-news-rss-raw-body-fetch.md
test -f docs/tasks/news-rss-raw-body-fetch/contract.md
test -f docs/tasks/news-rss-raw-body-fetch/handoff.md
test -f docs/tasks/news-rss-raw-body-fetch/review.md

grep -q "render_news_rss_raw_fetch_candidate_lookup_sql" src/stockanalysis/ingest/news/raw_fetch.py
grep -q "d.document_type = 'news_rss_item'" src/stockanalysis/ingest/news/raw_fetch.py
grep -q "raw_storage_uri" src/stockanalysis/ingest/news/raw_fetch.py
grep -q "ipaddress.ip_address" src/stockanalysis/ingest/news/raw_fetch.py
grep -q "HTTPRedirectHandler" src/stockanalysis/ingest/news/raw_fetch.py
grep -q "max_body_bytes" src/stockanalysis/ingest/news/raw_fetch.py
grep -q "paid_provider_api.*False" src/stockanalysis/ingest/news/raw_fetch.py
grep -q "live_llm_call.*False" src/stockanalysis/ingest/news/raw_fetch.py
grep -q "news-rss-raw-fetch" src/stockanalysis/ingest/cli.py
grep -q "verify_news_rss_raw_body_fetch.sh" docs/verification-plan.md

echo "news RSS raw body fetch verification passed"
