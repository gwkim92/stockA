# Review Notes

## Summary

- The global header now groups pages by operating flow instead of exposing every page as a flat numbered list.
- Global typography and card/list text now use safer Korean line wrapping and overflow behavior.
- Key copy now explains the product flow in operator language: data collection, news grouping, individual news AI candidates, recommendations, holding review, and trade safety.
- Individual news candidate analysis now has a stable `/ai-evidence` index, and each item links to `/ai-evidence/:id`.
- Mobile layouts now stack trace chains and stock rows instead of allowing page-level horizontal overflow.
- Future Codex OAuth news candidate outputs are instructed to write human-readable fields in Korean while preserving machine codes and tickers.

## Verification

- `cd apps/web && npm run typecheck`: pass.
- `cd apps/web && npm run build`: pass.
- `git diff --check`: pass.
- `PYTHONPATH=src python3 -m unittest tests.test_news_rss_ai_extract`: pass.
- EC2 browser smoke on `http://127.0.0.1:13000`: pass for the checked operating pages, with no server render error and no page-level horizontal overflow.

## Remaining Risks

- This slice does not change backend data, scoring, scheduler cadence, or broker/order flow.
- Existing DB artifacts generated before the Korean prompt change can still contain English source titles and English AI summaries until a data regeneration task is run.
