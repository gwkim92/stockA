# Review

## Verification

- Passed:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_recommendation_bootstrap tests.test_data_operations_cli tests.test_operating_data_orchestrator`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m awh verify --repo . --task recommendation-cycle-stack-components`
  - EC2 `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_recommendation_bootstrap tests.test_data_operations_cli tests.test_operating_data_orchestrator`
  - EC2 `recommendation-bootstrap --as-of-date 2026-05-22 --strategy-name long_term_core --horizon-type long_term --universe-version live-20260522 --market-code US --score-version bootstrap-v1`

## EC2 Smoke

- latest commit: `d877ae7`
- recommendation smoke: `run_id=584`, `status=succeeded`, `recommendation_count=6`, `score_component_count=60`.
- component validation:
  - every recommendation has 10 component rows.
  - component names are `cycle_score`, `macro_regime_score`, `domain_cycle_score`, `theme_cycle_score`, `instrument_cycle_score`, `cycle_conflict_penalty`, `momentum_score`, `short_term_score`, `rank_score`, `macro_flow_score`.
  - selected node is stored in cycle stack component explanation, for example `QUBT -> QUANTUM_COMPUTING_POLICY`, `NVDA -> AI_SEMICONDUCTOR_CYCLE`.
  - root `MARKET_NEWS_FLOW` is excluded from recommendation candidates.

## Risks

- 이번 slice는 저장 component 추가다. 화면 waterfall 개선은 별도 frontend task에서 이어가야 한다.
- 새 component들은 기본 weight 0이다. 실제 추천 total score 영향은 별도 승인/검증 전까지 주지 않는다.
