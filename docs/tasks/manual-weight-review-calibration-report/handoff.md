# Session Handoff

## Current Status

- 진행 중:
  - task contract를 만들었다.
  - `recommendation-weight-review-calibration-report-run` CLI를 추가했다.
  - source audit eval lookup, failure case lookup, report eval-run writer를 구현했다.
  - report는 manual review, automatic weight change, automatic order, broker submit 경계를 명시한다.
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
- Pending: EC2 smoke.

## Exact Next Step

- exact next step: EC2에 배포하고 `recommendation-weight-review-calibration-report-run --env-file /opt/stockanalysis/runtime/data-operations.env --as-of-date 2026-05-25 --audit-eval-run-id 16 --failure-case-limit 10 --execute`가 report eval run을 만들고 weight/order/broker flags를 false로 유지하는지 확인한다.
