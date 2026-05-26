# Session Handoff

## Current Status

- 진행 중:
  - task contract를 만들었다.
  - `recommendation-weight-review-calibration-report-run` CLI를 추가했다.
  - source audit eval lookup, failure case lookup, report eval-run writer를 구현했다.
  - report는 manual review, automatic weight change, automatic order, broker submit 경계를 명시한다.
  - EC2 smoke 중 `recommendation_date`보다 빠른 `measurement_end_date`가 failure case로 보이는 데이터 품질 문제를 발견했고, report 조회에서 invalid outcome window를 제외하도록 수정했다.
- 유지할 경계:
  - 추천 score/weight는 변경하지 않는다.
  - paper order approval, kill switch 해제, human approval 우회, broker submit은 하지 않는다.

## Expected EC2 Result

- 입력 audit eval은 `audit_eval_run_id=16`이다.
- 보고서는 manual review만 허용하고 automatic weight/order/broker submit은 모두 false로 표시해야 한다.
- component evidence상 신규 cycle/professional component가 positive spread를 입증하지 못하면 weight 증가는 제안하지 않아야 한다.

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_manual_weight_review_calibration_report tests.test_data_operations_cli`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- Passed: `git diff --check`
- Passed: `bash scripts/verify_project_execution_roadmap.sh`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task manual-weight-review-calibration-report`
- Passed on EC2:
  - Deployed commit: `dda6035 Filter invalid manual weight review failure cases`
  - Command: `recommendation-weight-review-calibration-report-run --env-file /opt/stockanalysis/runtime/data-operations.env --as-of-date 2026-05-25 --audit-eval-run-id 16 --failure-case-limit 10 --execute`
  - Result: `run_id=975`, `report_eval_run_id=18`, `decision=manual_review_allowed_keep_weights_collect_more_evidence`
  - Safety boundary: `automatic_weight_change_allowed=false`, `automatic_order_allowed=false`, `broker_submit_allowed=false`
  - Evidence: `eligible_for_manual_pilot_review_count=0`, `already_weighted_review_only_count=3`, `keep_zero_or_do_not_increase_count=12`

## Exact Next Step

- exact next step: `portfolio-risk-budget-policy-v2`를 시작해 섹터/테마 집중도, benchmark drift, position sizing, rebalance guardrail을 recommendation/paper validation 앞단에 붙인다. 추천 weight와 broker submit은 계속 변경하지 않는다.
