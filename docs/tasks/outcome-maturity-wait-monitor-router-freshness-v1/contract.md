# outcome-maturity-wait-monitor-router-freshness-v1 Contract

## Task Request

- request: `/data-health`의 outcome maturity wait monitor가 오래된 `recommendation_outcome_due_action_router` artifact의 `wait_until`을 최신 maturity 계산보다 우선하는 표시 불일치를 수정한다.
- context: EC2에서 최신 recommendation outcome calibration은 `eval-run-421`이고 다음 maturity due는 `2026-06-21`이다. 하지만 wait monitor는 오래된 due action router `eval-run-408` / source calibration `eval-run-27`의 `2026-07-19`를 보여줬다.

## Goal

- goal: wait monitor는 최신 DB 기반 `recommendation_outcome_maturity`와 그 `cadence_action`을 canonical로 사용하고, due action router는 같은 source calibration eval을 참조할 때만 보조 근거로 사용한다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/outcome-maturity-wait-monitor-router-freshness-v1/*`

## Invariants

- 추천 score, score component weight, benchmark definition, portfolio position, broker/order flow를 바꾸지 않는다.
- 실거래와 자동 주문은 계속 차단한다.
- 오래된 router artifact를 삭제하지 않고, 화면 판단에서만 최신 maturity와 일치하지 않는 router를 무시한다.

## Verification

- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_outcome_maturity_wait_monitor_ignores_stale_due_router_wait_until`
- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest tests.test_frontend_live_adapter`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-verify-venv/bin/python -m awh verify --repo . --task outcome-maturity-wait-monitor-router-freshness-v1`
- verification command: EC2 `/api/data-health` shows `outcome_maturity_wait_monitor.recommendation_next_due_date=2026-06-21` when maturity has that next due date and stale router still has `2026-07-19`.

## Done Criteria

- stale due action router cannot override current maturity/cadence wait date.
- `/data-health` remains healthy with `open_gates=[]`.
- order boundary remains `read_only_no_order`.
