# thesis-lifecycle-professional-gates-v1 Handoff

## Current Status

- 완료: thesis detail API/화면에 professional lifecycle gates를 추가했고 local/EC2 API/route/browser smoke가 통과했다.

## Intent

Thesis detail should enforce the professional investment lifecycle. A long-term thesis is not complete unless the buy case, catalysts, risks, invalidation conditions, valuation context, review cadence, and evidence freshness are visible and checked.

## Current Guardrails

- Do not change recommendation score weights.
- Do not add thesis write/edit APIs.
- Do not create orders or target weights.
- Do not enable broker submit or live orders.
- Use existing canonical/read adapter data first; no schema change in this slice.

## Implementation Notes

- Existing `/api/theses/{id}` already returns `lifecycle`, `evidence`, and `evidence_review`.
- Added `professional_lifecycle_gates` as a top-level read-only gate summary.
- Added evidence `observed_at` and normalized thesis evidence timestamps to UTC ISO where possible.
- Evidence freshness compares latest evidence `observed_at` with latest thesis review time where available.
- Missing dates are shown as warning instead of invented.
- Gate keys are stable in this order: `buy_case`, `catalysts`, `risks`, `invalidation`, `valuation`, `review_cadence`, `evidence_freshness`, `order_boundary`.
- Every gate preserves `automatic_order_allowed=false`, `broker_submit_allowed=false`, and `order_boundary=read_only_no_order`.
- `/theses/[thesisId]` renders a Korean "전문 Thesis Gate" section above the existing lifecycle detail.

## Verification

- Focused backend:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_thesis_detail_response_matches_frontend_contract_shape`
  - Result: `Ran 1 test ... OK`
- Adapter suite:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - Result: `Ran 59 tests ... OK`
- Full backend:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`
  - Result: `Ran 940 tests ... OK`
- Compile/type/build:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - Result: passed
- Roadmap/harness:
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task thesis-lifecycle-professional-gates-v1`
  - `git diff --check`
  - Result: passed
- EC2 deploy:
  - `/opt/stockanalysis/app` fast-forwarded to commit `b2dba33`.
  - Focused thesis detail test: `Ran 1 test ... OK`
  - `apps/web` `npm run typecheck` and `npm run build`: passed
  - `stockanalysis-frontend-api.service` and `stockanalysis-web.service`: active
- EC2 API smoke:
  - `/api/theses/thesis-28`
  - `professional_lifecycle_gates.status=complete`
  - gate count `8`
  - gate keys: `buy_case`, `catalysts`, `risks`, `invalidation`, `valuation`, `review_cadence`, `evidence_freshness`, `order_boundary`
  - `latest_evidence_at=2026-05-23T21:16:53Z`
  - `evidence_observed_at_count=1`
  - `order_boundary=read_only_no_order`, `automatic_order_allowed=false`, `broker_submit_allowed=false`
- EC2 route/browser smoke through `http://127.0.0.1:13000`:
  - `/theses/thesis-28`: `200`
  - contains `전문 Thesis Gate`, `왜 보유하는가`, `무엇이 맞아야 하는가`, `무엇을 조심해야 하는가`, `무엇이 틀리면 나가는가`, `가격이 합리적인가`, `언제 다시 보는가`, `최근 근거가 검토에 반영됐는가`, `읽기 전용·주문 금지`

## Remaining Work

- The gates are read-only and do not create or update thesis records.
- The valuation gate still checks valuation context existence only; target price range and scenario math remain next.

## Exact Next Step

- exact next step: open `valuation-target-range-foundation-v1` and make valuation snapshots expose target range, upside/downside, scenario assumptions, and margin-of-safety evidence without score or order changes.
