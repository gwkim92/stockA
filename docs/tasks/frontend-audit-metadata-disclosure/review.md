# Task Review

## Summary

- Added reusable `AuditMetadata` disclosure component for collapsed raw trace data.
- Recommendation score cards now show user-facing evidence labels/links first; raw score component, evidence, run, universe, and feature IDs are available under "추적 ID 보기".
- Thesis evidence cards now show "성과 근거 보기" and "이벤트 원장 열기" first; raw evidence IDs are available under "추적 ID 보기".
- Added CSS for long audit metadata values so IDs and JSON-like rules wrap instead of overflowing.
- API contract, DB schema, recommendation scoring/action, trading, and scheduler behavior were not changed.

## Verification Evidence

- `cd /Users/woody/ai/stockanalysis/apps/web && npm run typecheck && npm run build`: passed.
- Browser smoke `/theses/AAPL-bootstrap-v1`: default view hides `performance-outcome-*`/`event-*` IDs and shows meaningful links; screenshot saved at `/private/tmp/stockanalysis-runtime/frontend-audit-metadata-disclosure-thesis.png`.
- Browser smoke `/recommendations/AAPL-2024-11-01`: default view hides `market-feature-*`, `universe-rank-*`, and `pipeline-run-*` IDs and shows meaningful labels/links; screenshot saved at `/private/tmp/stockanalysis-runtime/frontend-audit-metadata-disclosure-recommendation.png`.
- Browser click on "추적 ID 보기" confirmed raw metadata remains available.

## Residual Risks

- Rule reason codes such as `recommendation_bucket_avoid` are still visible in thesis review rationale parentheses for auditability. A later pass should render them as separate chips or move them into the same metadata disclosure pattern.
- Market feature/rank provenance currently has no dedicated detail route, so those cards show "연결 화면 없음" while preserving raw provenance in metadata.
