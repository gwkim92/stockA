# Review: news-ai-evidence-quality-pipeline

## Review Notes

- Added a backend news AI extraction runner with fixture and `codex_oauth` provider boundaries.
- Added validator-gated writes: AI output is stored as `news_event_candidate` before canonical theme/instrument impacts are upserted.
- Stored human-readable `extracted_fields` in the news AI artifact so the existing `/ai-evidence/...` page can display summary, theme impacts, instrument impacts, and uncertainty.
- Kept the existing local rule enrichment path as fallback/baseline and did not change recommendation scoring, benchmark, DB migrations, or broker/order flow.
- Candidate-level AI failure now returns `completed_with_fallback` without failing the operations CLI process, so timers can continue while failures remain visible in run output.
- Updated event-intelligence orchestration references to call `news-rss-ai-extract-run --provider codex_oauth --limit 10 --execute`.
- Verification passed with Python 3.13 verify venv, AWH readiness, focused verify script, Next typecheck, and Next build.
