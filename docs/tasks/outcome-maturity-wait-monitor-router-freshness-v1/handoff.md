# outcome-maturity-wait-monitor-router-freshness-v1 Handoff

## Status

- status: in_progress
- current status: implementation started locally.
- in progress: code and unit test are being verified.

## Current Status

- 기준일: 2026-06-20.
- 발견한 문제:
  - `recommendation_outcome_maturity`는 최신 calibration `eval-run-421` 기준으로 `next_due_date=2026-06-21`을 계산했다.
  - `outcome_maturity_wait_monitor`는 오래된 due action router `eval-run-408`, source calibration `eval-run-27`의 `wait_until=2026-07-19`를 우선해 사용자에게 틀린 다음 주기를 보여줬다.
- 수정 방향:
  - due action router의 `source_calibration_eval_run_id`가 current maturity의 `source_calibration_eval_run_id`와 같을 때만 router를 보조 근거로 사용한다.
  - 다르면 current maturity의 `cadence_action.wait_until`과 `next_due_date`를 우선한다.

## Verification

- pending: local tests and EC2 smoke.

## Next Step

- exact next step: run local tests, commit/push to `develop`, deploy to EC2, and verify `/api/data-health` wait monitor date no longer shows stale `2026-07-19`.
