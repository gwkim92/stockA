# Task Review

## Summary

- `apps/web/src/lib/korean-labels.ts`에 embedded token replacement를 추가해 긴 문장 안의 `long_term_core`, `avoid`, `exclude`, `ANNUAL_REPORTING`, `forming`, `unavailable`, `read-only`, `cycle`, `feature`, `source_run_id` 같은 내부 표현을 한국어로 치환한다.
- thesis 상세의 version badge와 무효화 조건 렌더링을 사용자용 한국어 label 경로로 바꿨다.
- recommendation 상세의 score version과 market feature 설명을 한국어 운영 문구로 바꿨다.
- API contract, DB schema, scoring, recommendation action, LLM/RAG, trading, scheduler는 변경하지 않았다.

## Verification Evidence

- `cd /Users/woody/ai/stockanalysis/apps/web && npm run typecheck`: passed.
- `cd /Users/woody/ai/stockanalysis/apps/web && npm run build`: passed.
- Browser smoke `/theses/AAPL-bootstrap-v1`: strategy/action/theme/cycle/invalidation/read-only wording improved; screenshot saved at `/private/tmp/stockanalysis-runtime/frontend-domain-language-normalization-thesis.png`.
- Browser smoke `/recommendations/AAPL-2024-11-01`: strategy/action/score-version/gate/provenance wording improved; screenshot saved at `/private/tmp/stockanalysis-runtime/frontend-domain-language-normalization-recommendation.png`.

## Residual Risks

- Audit IDs such as `performance-outcome-1`, `market-feature-aapl-*`, `pipeline-run-*` remain visible where they serve traceability. A later UI pass should move them behind "metadata/details" affordances if the screen feels too technical.
- This does not rewrite stored backend summary rows; it normalizes presentation at the frontend label layer.
