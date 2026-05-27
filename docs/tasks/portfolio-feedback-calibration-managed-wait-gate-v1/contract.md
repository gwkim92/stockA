# portfolio-feedback-calibration-managed-wait-gate-v1 Contract

## Task Request

- request: 남은 `portfolio_review_feedback_calibration_attention`을 운영 장애처럼 보이지 않게 정리하되, 추천 weight 변경 차단은 유지한다.
- context: 현재 EC2 운영 후보 상태에서 auth/RBAC, alert, data runner, quality audit gate는 닫혔고 남은 gate는 outcome feedback 성숙 대기다.

## Goal

- goal: 성과 관찰 기간을 기다리는 상태는 `managed_wait`로 표시하고 open gate에서 제외한다. 단, recommendation weight 변경과 broker/order flow는 계속 차단한다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/portfolio-feedback-calibration-managed-wait-gate-v1/*`

## Invariants

- Do not change recommendation scoring weights.
- Do not change benchmark, portfolio positions, paper/live broker order flow, or broker submit.
- Do not mark weight review as allowed while outcome feedback is immature.
- Do not hide the maturity date, sample gaps, or weight-review block reason.

## Scope

- Add a managed wait policy to portfolio review feedback calibration.
- Close only the open gate representation when the router says to wait and all safety guardrails remain read-only.
- Keep `weight_review_blocked=true`.
- Expose Korean wording that this is “관리된 대기” rather than an operational failure.

## Verification

- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task portfolio-feedback-calibration-managed-wait-gate-v1`
- verification command: `git diff --check`

## Done Criteria

- [ ] Managed outcome-window wait no longer appears in `open_gates`.
- [ ] `weight_review_blocked` remains true while outcome feedback is immature.
- [ ] `/data-health` explains the managed wait state in user-facing Korean.
- [ ] EC2 smoke confirms only true operational/investment blockers remain open.
