# Task Contract

## Task

- 이름: recommendation-quality-calibration
- 요청: 추천 component가 실제 outcome/paper validation과 얼마나 맞는지 평가하되, 추천 점수 weight는 변경하지 않는다.
- 담당: Codex
- 날짜: 2026-05-24

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `stockanalysis-operations recommendation-quality-eval-run --as-of-date YYYY-MM-DD --horizon 30d`가 추천, score component, performance outcome, paper validation 상태를 읽어 평가 리포트를 만들고, `--execute` 시 `ai.eval_run`과 `ops.pipeline_run`에 저장한다.

## Scope

- 포함:
  - read-only recommendation quality lookup SQL
  - component별 sample count, positive/negative 평균 score, spread, coverage
  - outcome coverage, 평균 수익률/알파, paper validation 최신 상태
  - cycle stack component weight가 아직 0인지 확인하는 guardrail
  - CLI와 unit/CLI tests
- 제외:
  - 추천 점수 산식/weight 변경
  - 추천 row 재생성
  - paper order 생성/제출
  - frontend redesign
  - Codex OAuth 호출

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/recommendation_quality_eval.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `tests/test_recommendation_quality_eval.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_data_operations_cadence.py`
  - `tests/test_operating_data_orchestrator.py`
  - `docs/tasks/recommendation-quality-calibration/*`
- 수정 금지 파일:
  - `src/stockanalysis/signal/recommendation.py` scoring weights
  - DB scoring migrations
  - broker/order submit path
  - `.env` secret values

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_recommendation_quality_eval tests.test_data_operations_cli`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-quality-calibration`

## Done Criteria

- 평가 runner는 추천 산식이나 component weight를 변경하지 않는다.
- 평가 결과는 sample size가 부족하면 `insufficient_sample`로 표시한다.
- `macro_regime_score`, `domain_cycle_score`, `theme_cycle_score`, `instrument_cycle_score`, `cycle_conflict_penalty`는 설명력 측정 대상이지만 총점 weight 변경 대상이 아니다. 기존 `cycle_score`와 이미 허용된 `macro_flow_score`는 이 zero-weight guardrail에 포함하지 않는다.
- `--execute`는 `ai.eval_run`과 `ops.pipeline_run`만 기록한다.
