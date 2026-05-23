# Review

## Verification

- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- Local rendered check with API tunnel:
  - Desktop screenshot: `/private/tmp/stockanalysis-runtime/intelligence-signal-density-final.png`
  - Mobile screenshot: `/private/tmp/stockanalysis-runtime/intelligence-signal-density-mobile.png`

## Result

- `/intelligence` no longer fails because `/api/remediation-tickets` is unavailable.
- Main page text now explains the screen purpose as news flow and recommendation linkage review.
- Per-cluster cards are shorter and show the direct reason for grouping, stock/theme relationship, recommendation use, and representative translated news blocks.
- Mobile layout stacks correctly.

## Risks

- This task does not implement stored approve/reject review actions.
- If API data itself is stale or misclassified, this UI still shows that data; data quality cleanup remains a backend/ingest task.
