# professional-coverage-refresh-after-source-remediation-v1 Review

## Review Summary

- Completed. Professional coverage was refreshed after source cleanup, stale ARM segment pollution stayed absent, EROK and SPY are now explicit source/model blockers, and frontend stock/recommendation pages render the blocker reason directly. Recommendation scoring weights and broker/order boundaries were not changed.

## Issues Found

- SPY cannot be treated as a normal company for financial statement modeling. It is a fund-like product; this task now labels that fact instead of hiding it, but full ETF/fund analysis needs a separate lane.
- EROK currently lacks SEC `facts.us-gaap` financial statement taxonomy in companyfacts. The system now surfaces this as `sec_companyfacts_missing_us_gaap_facts`, not as a parser failure.

## Residual Risks

- Professional coverage is sufficient for weight-review readiness checks (`39/45 = 0.866667`) but not complete. Gap examples remain SPY and EROK for different reasons.
- `ready_for_weight_review` is an evaluation status only. It does not authorize automatic scoring weight changes.
- Live broker submit remains out of scope and disabled.

## Verification Evidence

- Local verification before UI commit `a2f2c0c`:
  - `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter` -> `Ran 60 tests OK`
  - `PYTHONPATH=src python3 -m compileall -q src tests` -> passed
  - `cd apps/web && npm run typecheck` -> passed
  - `cd apps/web && npm run build` -> passed
  - `git diff --check` -> passed
- EC2 verification after fast-forward to `a2f2c0c`:
  - `/opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter` -> `Ran 60 tests OK`
  - `cd apps/web && npm run typecheck` -> passed
  - `cd apps/web && npm run build` -> passed
  - `stockanalysis-frontend-api.service` -> `active`
  - `stockanalysis-web.service` -> `active`
  - `http://127.0.0.1:8787/__health` -> HTTP response captured, 642 bytes
- EC2 data evidence:
  - coverage refresh `run_id=1519`, status `completed_with_failures`; downstream runs `1522` through `1530` succeeded.
  - post-decision refresh `run_id=1565`, status `completed_with_failures`.
  - recommendation component rerun `run_id=1579`, status `completed`.
  - recommendation quality eval `run_id=1580`, `eval_run_id=25`, `quality_status=ready_for_weight_review`, `sample_status=sufficient_sample`, `recommendation_count=45`, `outcome_count=30`, professional coverage `39/45 = 0.866667`.
- Route smoke through `http://127.0.0.1:13000`:
  - `/stocks/SPY` contains `기업 재무 모델 비적용` or `펀드형 상품`.
  - `/stocks/EROK` contains `SEC companyfacts` or `재무 facts`.
  - `/recommendations/recommendation-157` contains `기업 재무 모델 비적용` or `펀드형 상품`.
  - `/stocks/ARM` contains financial model wording and does not contain `Customer A`, `Customer B`, or `Entity Wide`.
