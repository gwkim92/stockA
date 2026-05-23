# Task Contract

## Task

- 이름: recommendation-cycle-stack-components
- 요청: 추천 점수 구성요소를 거시/도메인/테마/종목 사이클 stack으로 분해해 저장한다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 추천 row마다 기존 점수 component에 더해 `macro_regime_score`, `domain_cycle_score`, `theme_cycle_score`, `instrument_cycle_score`, `cycle_conflict_penalty`가 저장되고, 기존 총점 산식은 급격히 바뀌지 않는다.

## Scope

- 포함:
  - recommendation candidate lookup에 `signal.cycle_hierarchy_state_snapshot` 입력 추가
  - 추천 component row 추가
  - weight 0 기반 conservative rollout
  - unit 검증
- 제외:
  - frontend waterfall UI 재구성
  - broker/live order flow
  - AI가 직접 추천 점수 결정
  - 기존 benchmark/evaluation split 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/signal/recommendation.py`
  - `tests/test_recommendation_bootstrap.py`
  - `docs/tasks/recommendation-cycle-stack-components/`
- 수정 금지 파일:
  - `.env`와 secret 값
  - broker/live order submission
  - benchmark/evaluation split

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_recommendation_bootstrap tests.test_data_operations_cli tests.test_operating_data_orchestrator`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m awh verify --repo . --task recommendation-cycle-stack-components`

## Done Criteria

- 기존 recommendation bootstrap이 새 component rows를 저장한다.
- 새 component weight는 기본 0으로 시작해 총점 급변을 막는다.
- `macro_flow_score` 기존 feature flag/weight는 유지한다.
- 테스트가 새 component count와 SQL provenance 입력을 검증한다.
