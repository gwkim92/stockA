# outcome-maturity-wait-monitor-router-freshness-v1 Handoff

## Status

- status: completed
- current status: implemented, pushed to `develop`, deployed to EC2, and smoke verified.
- completed: wait monitor now prefers current maturity/cadence over stale due action router artifacts.

## Current Status

- 기준일: 2026-06-20.
- 발견한 문제:
  - `recommendation_outcome_maturity`는 최신 calibration `eval-run-421` 기준으로 `next_due_date=2026-06-21`을 계산했다.
  - `outcome_maturity_wait_monitor`는 오래된 due action router `eval-run-408`, source calibration `eval-run-27`의 `wait_until=2026-07-19`를 우선해 사용자에게 틀린 다음 주기를 보여줬다.
- 수정 방향:
  - due action router의 `source_calibration_eval_run_id`가 current maturity의 `source_calibration_eval_run_id`와 같을 때만 router를 보조 근거로 사용한다.
  - 다르면 current maturity의 `cadence_action.wait_until`과 `next_due_date`를 우선한다.

## Verification

- passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_outcome_maturity_wait_monitor_ignores_stale_due_router_wait_until`
- passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest tests.test_frontend_live_adapter`
- passed: `git diff --check`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-verify-venv/bin/python -m awh verify --repo . --task outcome-maturity-wait-monitor-router-freshness-v1`
- passed: deployed commit `a4b93ccf` to EC2 via `git pull --ff-only origin develop`.
- passed: EC2 `python -m compileall -q src` and `stockanalysis-frontend-api.service` restart.
- passed: EC2 `/api/data-health` has `open_gates=[]`.
- passed: EC2 `outcome_maturity_wait_monitor.recommendation_next_due_date=2026-06-21`, `earliest_action_date=2026-06-21`, and `recommendation_due_action_router_current=false` while stale router still has `wait_until=2026-07-19`.
- passed: EC2 `/__health`, `/__ready`, `/`, `/data-health`, `/admin/ai-agents`, `/market-map`, `/cycle-map`, `/recommendations`, `/paper-trading` returned 200.

## Next Step

- exact next step: wait for the next recommendation outcome window on 2026-06-21 and monitor the next `news-intraday` timer. Do not start manual weight review without a separate approved task.
