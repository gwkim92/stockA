# Session Handoff

## Current Status

- 완료:
  - task contract를 만들었다.
  - `recommendation-quality-eval-run`에 professional analysis coverage guardrail을 추가했다.
  - eval SQL이 active recommendation별 재무지표, 피어 비교, 밸류에이션, 산업 경쟁 위치, 기업 리서치 artifact, active thesis coverage를 집계한다.
  - scoring gate가 complete professional coverage rate 기준 미만이면 outcome 표본이 충분해도 `ready_for_weight_review`를 막는다.
  - CLI flag `--min-professional-coverage-rate`를 추가했다.
  - unit/CLI regression, compile, diff, AWH 검증을 통과했다.
- 진행 중:
  - 없음.
- 막힌 점:
  - 없음.

## Decisions

- 이 작업은 추천 weight를 조정하지 않는다.
- professional coverage는 active recommendation 기준으로 본다.
- 첫 기준은 complete professional coverage rate가 80% 이상일 때만 weight review 후보가 될 수 있게 한다.
- coverage gap은 실패가 아니라 “추천 weight 검토 금지 사유”로 남긴다.

## Exact Next Step

- exact next step: EC2에 배포 후 `recommendation-quality-eval-run --as-of-date 2026-05-25 --horizon 30d --min-sample-size 20 --execute` smoke를 실행해 실제 active recommendation coverage가 어떻게 나오는지 확인한다.

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_recommendation_quality_eval`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_data_operations_cli.DataOperationsCliTests.test_recommendation_quality_eval_run_command_passes_env_horizon_and_writes_output`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_recommendation_quality_eval tests.test_data_operations_cli`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- Passed: `git diff --check`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-quality-professional-coverage-guardrail`

## Residual Risk

- EC2 smoke는 아직 실행 전이다.
- 이 guardrail은 분석 coverage를 평가할 뿐, 부족한 coverage를 자동 생성하지는 않는다.
