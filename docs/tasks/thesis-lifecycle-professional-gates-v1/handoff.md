# thesis-lifecycle-professional-gates-v1 Handoff

## Current Status

- 완료: thesis detail API/화면에 professional lifecycle gates를 추가했고 로컬 검증을 통과했다. EC2 배포와 route smoke는 아직 남아 있다.

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

## Remaining Work

- Run roadmap verifier, AWH verifier, and `git diff --check`.
- Deploy to EC2 and smoke `/api/theses/{id}` plus `/theses/{id}` through `127.0.0.1:13000`.

## Exact Next Step

- exact next step: run `bash scripts/verify_project_execution_roadmap.sh` and AWH verification for `thesis-lifecycle-professional-gates-v1`, then deploy and smoke EC2.
