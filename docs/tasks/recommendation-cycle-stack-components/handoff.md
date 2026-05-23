# Session Handoff

## Current Status

- 완료:
  - `RecommendationCandidate`에 macro/domain/theme/instrument cycle stack fields와 `cycle_conflict_penalty`를 추가했다.
  - recommendation candidate lookup SQL이 `signal.cycle_hierarchy_state_snapshot`에서 theme/domain/macro cycle score를 읽도록 확장됐다.
  - `signal.recommendation_score_component`에 `macro_regime_score`, `domain_cycle_score`, `theme_cycle_score`, `instrument_cycle_score`, `cycle_conflict_penalty`를 추가 저장한다.
  - 새 stack component 기본 weight는 0으로 둬 기존 total score 급변을 막았다.
  - unit/AWH 검증을 통과했다.
- 막힌 점:
  - 없음.

## Exact Next Step

- exact next step: EC2에 배포한 뒤 `recommendation-bootstrap` smoke를 실행해 기존 batch가 새 10개 component rows를 저장하는지 확인한다.
