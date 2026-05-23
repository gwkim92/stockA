# Session Handoff

## Current Status

- 완료:
  - `RecommendationCandidate`에 macro/domain/theme/instrument cycle stack fields와 `cycle_conflict_penalty`를 추가했다.
  - recommendation candidate lookup SQL이 `signal.cycle_hierarchy_state_snapshot`에서 theme/domain/macro cycle score를 읽도록 확장됐다.
  - `signal.recommendation_score_component`에 `macro_regime_score`, `domain_cycle_score`, `theme_cycle_score`, `instrument_cycle_score`, `cycle_conflict_penalty`를 추가 저장한다.
  - 새 stack component 기본 weight는 0으로 둬 기존 total score 급변을 막았다.
  - component explanation에 선택된 recommendation node code를 저장해 추천 근거 추적성을 보강했다.
  - `MARKET_NEWS_FLOW` root는 추천 후보에서 제외했다.
  - `US_MARKET_BREADTH`는 ETF에는 허용하되 개별주 추천 node로 직접 쓰지 않게 필터링했다.
  - unit/AWH 검증을 통과했다.
  - EC2 `/opt/stockanalysis/app`를 `d877ae7`까지 fast-forward했다.
  - EC2에서 2026-05-22 recommendation bootstrap을 재실행해 `run_id=584`, recommendation 6 rows, score component 60 rows를 저장했다.
- 막힌 점:
  - 없음.

## Exact Next Step

- exact next step: frontend detail에서 10개 component와 선택 node를 한국어 waterfall로 보여주는 `frontend-cycle-map-experience`/recommendation detail pass를 진행한다.
