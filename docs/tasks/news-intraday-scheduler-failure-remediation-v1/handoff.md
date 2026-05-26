# news-intraday-scheduler-failure-remediation-v1 Handoff

## Status

- in progress: root cause found and local fix implemented; EC2 deploy/rerun is next.

## Context

- EC2 FastAPI and Next.js services are active.
- EC2 profile timers are active.
- `stockanalysis-operating-data-news-intraday.service` last result is `exit-code`.
- This blocks a full claim that news collection and AI analysis are automatically healthy.
- Root cause: `news-rss-daily-run` failed on the `yahoo-finance-news` feed with PostgreSQL `ON CONFLICT DO UPDATE command cannot affect row a second time`.
- The failing feed emitted duplicate `external_document_id` rows in one ingest batch, and `render_news_rss_upsert_sql` attempted to upsert them in a single statement without pre-deduplication.

## Exact Next Step

- exact next step: deploy the SQL dedupe fix to EC2, start `stockanalysis-operating-data-news-intraday.service`, and verify data-health no longer reports the unexplained `exit-code` state.

## Implementation Notes

- Updated `src/stockanalysis/ingest/news/sql.py`.
- Added `input_deduped` CTE with `distinct on (external_document_id)` before `ingest.source_document` and `event.event` upserts.
- Added output counters `deduped_item_count` and `duplicate_item_count`.
- Added unit coverage in `tests/test_news_rss.py` for duplicate RSS item IDs.

## Local Verification So Far

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss tests.test_news_rss_feed_runner tests.test_data_operations_cli`
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not hide the scheduler failure by only changing UI labels.
- Do not introduce paid providers.
