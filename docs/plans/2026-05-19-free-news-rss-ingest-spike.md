# Free News RSS Ingest Spike Plan

## Summary

- Add a no-cost RSS/Atom ingest path that writes feed items into the existing source document and event evidence tables.
- Keep this as an operations/backend slice, not a frontend-only or shell-only feature.
- Do not change DB schema, scoring, recommendation quality gates, or broker execution.

## Implementation

- Add `rss_news` source adapter with a credential-free `feed` dataset.
- Add `stockanalysis.ingest.news.rss` parser for RSS 2.0 and Atom entries using stdlib XML parsing.
- Add `stockanalysis.ingest.news.upsert` and SQL renderer for source document + basic event + document link upsert.
- Add CLI commands:
  - `news-rss-sync` prints parsed fixture/live feed summary.
  - `news-rss-upsert` writes parsed items into canonical Postgres through the existing psql executor.
- Add data operations cadence visibility for `news_rss_upsert` so `/data-health` can show missing/stale news collection status through the existing expected-job mechanism.
- Add fixture tests and CLI tests.

## Guardrails

- No external paid provider dependency.
- No scraping bypass or logged secrets.
- No AI buy/sell decisions.
- No broker or order table writes.
