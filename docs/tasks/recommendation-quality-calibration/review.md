# Review

## Result

- 로컬 구현과 검증 완료.
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

## Remaining Risk

- 실제 calibration 결론은 충분한 outcome sample이 쌓인 뒤에만 신뢰할 수 있다.
- sample size가 작으면 runner는 `needs_more_data`로 표시하며 weight 변경은 금지 상태로 남는다.
