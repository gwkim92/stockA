# Review

## Result

- 로컬 구현, EC2 반영, 실제 DB smoke 완료.
- 새 CLI: `stockanalysis-operations recommendation-quality-eval-run --as-of-date YYYY-MM-DD --horizon 30d`
- 평가 입력:
  - `signal.recommendation`
  - `signal.recommendation_score_component`
  - `performance.recommendation_outcome`
  - 최신 `trading.paper_validation_run`
- 저장 경로:
  - `ops.pipeline_run.pipeline_name='recommendation_quality_eval'`
  - `ai.eval_run.eval_name='recommendation_quality_calibration'`
- 산출 지표:
  - outcome coverage
  - positive outcome rate
  - 평균 absolute return, alpha, drawdown
  - component별 positive/non-positive 평균 score와 spread
  - cycle component weight가 0으로 유지되는지 guardrail
  - paper validation 최신 status/conflict count
- 추천 산식과 component weight는 변경하지 않았다.
- guardrail은 새로 추가된 zero-weight 보호 대상인 `macro_regime_score`, `domain_cycle_score`, `theme_cycle_score`, `instrument_cycle_score`, `cycle_conflict_penalty`만 본다. 기존 `cycle_score`와 이미 허용된 `macro_flow_score`는 오탐 방지를 위해 제외했다.

## EC2 Evidence

- commit: `d31d99c fix: narrow recommendation cycle weight guardrail`
- smoke command: `recommendation-quality-eval-run --as-of-date 2026-05-24 --horizon 30d --min-sample-size 20 --execute`
- result:
  - `run_id=705`
  - `eval_run_id=3`
  - `quality_status=needs_more_data`
  - `sample_status=insufficient_sample`
  - `recommendation_count=30`
  - `outcome_count=0`
  - protected cycle weight guardrail: `cycle_weight_unchanged=true`
  - latest paper validation: `failed`, conflicts `3`

## Remaining Risk

- 실제 calibration 결론은 충분한 outcome sample이 쌓인 뒤에만 신뢰할 수 있다.
- sample size가 작으면 runner는 `needs_more_data`로 표시하며 weight 변경은 금지 상태로 남는다.
- 현재 EC2 데이터에는 30일 horizon outcome이 아직 없어 component별 설명력 판단은 보류 상태다.
- 최신 paper validation이 failed라서 사용자가 페이퍼 거래 상태를 명확히 이해하도록 `decision-cockpit-ux-v2`에서 화면 정리가 필요하다.
