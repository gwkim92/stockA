# news-intraday-scheduler-failure-remediation-v1 Review

## Review Summary

- Local root-cause review passed. The failure was not systemd, OAuth, or scheduler identity; it was duplicate RSS item IDs entering one SQL upsert statement.

## Issues Found

- EC2 report `/opt/stockanalysis/runtime/operating-data-profile-scheduler-reports/news-intraday-operating-data-run.json` showed failed step `news-rss-ingest`.
- Artifact `20260526T180011Z_news-rss-daily/stdout.txt` showed `yahoo-finance-news` failed with PostgreSQL `ON CONFLICT DO UPDATE command cannot affect row a second time`.
- Local fix adds SQL pre-dedupe before source document/event upserts.

## Residual Risks

- EC2 rerun is still pending.
- The fix prevents duplicate IDs inside a single feed batch, but separate downstream quality issues remain in `cycle_ai_quality_audit`.

## Verification Evidence

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss tests.test_news_rss_feed_runner tests.test_data_operations_cli`
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
