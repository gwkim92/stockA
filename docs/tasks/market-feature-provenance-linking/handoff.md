# Session Handoff

## Active Task

- 이름: market-feature-provenance-linking
- 담당: Codex
- 날짜: 2026-05-20

## Current Status

- 완료:
  - task contract created.
  - implementation plan created.
  - `render_frontend_recommendation_detail_state_sql()` now builds `market_feature_provenance`, `strategy_universe_provenance`, and `score_component_rows` CTEs.
  - `momentum_score` maps to `return_since_first_observation`; `short_term_score` maps to `return_1d`.
  - `rank_score` now uses `universe-rank-*` provenance instead of being mislabeled as a market feature.
  - Recommendation score component DTOs now include additive `provenance` objects.
  - Recommendation evidence review now checks market/rank provenance as a separate gate.
  - Recommendation detail page renders feature code, source run, observation window, and universe rank in Korean.
  - Frontend recommendation detail example includes provenance payloads.
- 진행 중:
  - none.
- 막힌 점:
  - none currently.

## Exact Next Step

- 다음 세션은 이것부터 시작: recommendation/thesis generation quality로 넘어가기 전에, 필요하면 `market-feature-*` 전용 상세 화면 또는 feature snapshot list API를 별도 task로 설계한다.

## Verification

- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter -v` passed.
- `cd apps/web && npm run typecheck` passed.
- `cd apps/web && npm run build` passed.
- Live API smoke: `/api/recommendations/AAPL-2024-11-01` returned `quality_status=ready_for_human_review`, `pass_count=6`, `market_or_rank_component_count=3`, `market_or_rank_provenance_count=3`.
- Live API component provenance:
  - `momentum_score`: `market_feature`, `return_since_first_observation`, `pipeline-run-8`.
  - `rank_score`: `strategy_universe_rank`, rank `2/3`, `pipeline-run-7`.
  - `short_term_score`: `market_feature`, `return_1d`, `pipeline-run-8`.
- Browser check: `/recommendations/AAPL-2024-11-01` renders Korean score provenance. Screenshot: `/private/tmp/stockanalysis-runtime/market-feature-provenance-linking.png`.

## Risks

- 이 작업은 이미 생성된 score를 설명하는 read-only provenance다. 점수 산식이 해당 row를 causally 사용했다는 별도 감사 증빙까지 생성하지는 않는다.
- live DB에 feature snapshot/source_run_id가 비어 있으면 provenance는 fallback 형태로 표시될 수 있다.
- No DB schema, scoring, benchmark, provider call, broker/order, or scheduler behavior changed.
