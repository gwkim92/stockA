# news-intraday-scheduler-failure-remediation-v1 Handoff

## Status

- completed: root cause found, local fix implemented, EC2 deployed, `news-intraday` rerun succeeded, and data-health scheduler status now reports success.

## Context

- EC2 FastAPI and Next.js services are active.
- EC2 profile timers are active.
- `stockanalysis-operating-data-news-intraday.service` last result is `exit-code`.
- This blocks a full claim that news collection and AI analysis are automatically healthy.
- Root cause: `news-rss-daily-run` failed on the `yahoo-finance-news` feed with PostgreSQL `ON CONFLICT DO UPDATE command cannot affect row a second time`.
- The failing feed emitted duplicate `external_document_id` rows in one ingest batch, and `render_news_rss_upsert_sql` attempted to upsert them in a single statement without pre-deduplication.

## Exact Next Step

- exact next step: move to `cycle-ai-quality-audit-contamination-remediation-v1`, because data-health still reports AI evidence quality issues such as ungrounded direct tickers and macro false ticker counts.

## Implementation Notes

- Updated `src/stockanalysis/ingest/news/sql.py`.
- Added `input_deduped` CTE with `distinct on (external_document_id)` before `ingest.source_document` and `event.event` upserts.
- Added output counters `deduped_item_count` and `duplicate_item_count`.
- Added unit coverage in `tests/test_news_rss.py` for duplicate RSS item IDs.

## Local Verification So Far

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss tests.test_news_rss_feed_runner tests.test_data_operations_cli`
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task news-intraday-scheduler-failure-remediation-v1`

## EC2 Verification

- Deployed commit: `bed027e`.
- Command: `sudo systemctl start stockanalysis-operating-data-news-intraday.service`.
- Result: service exited `status=0/SUCCESS`.
- Output report: `/opt/stockanalysis/runtime/operating-data-profile-scheduler-reports/news-intraday-operating-data-run.json`.
- Report result: `run_status=completed`, `failed_step_count=0`.
- Succeeded steps: `news-rss-ingest`, `news-missing-instrument-bootstrap`, `news-rss-enrichment`, `news-korean-translation`, `news-cluster-evidence`, `news-ai-evidence`, `macro-event-propagation`, `hierarchical-impact-propagation`.
- `/api/data-health` scheduler profile for `news-intraday`: `last_result=success`, `active_state=active`, next elapse `2026-05-26T20:00:00Z`.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not hide the scheduler failure by only changing UI labels.
- Do not introduce paid providers.
