# professional-analysis-next-action-cockpit-v1 Handoff

## Status

- status: implemented_and_ec2_smoked
- started_at: 2026-05-27
- current status: implemented, committed, pushed, deployed to EC2, and smoke verified.
- completed: API payload `professional_analysis_next_action`.
- completed: `/data-health` professional next-action section.

## Current Decision

- Build the summary from existing canonical data-health payloads instead of adding new database tables.
- Keep EROK-like source blockers visible but already excluded from professional decision and paper validation inputs.

## Next Step

- exact next step: continue using the professional next-action section to decide between source remediation, outcome wait, and future manual weight review; do not introduce paid external tooling yet.

## Verification So Far

- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task professional-analysis-next-action-cockpit-v1`
- passed: `git diff --check`
- passed: EC2 targeted tests with `/opt/stockanalysis/venv/bin/python`.
- passed: EC2 Next typecheck and production build.
- passed: EC2 service restart with `stockanalysis-frontend-api.service=active` and `stockanalysis-web.service=active`.

## EC2 Verification

- deployed commit: `388034e`.
- `/api/data-health`: `professional_analysis_next_action.status=managed_outcome_wait`, `title=전문 분석은 관리 중, 성과 표본 대기`, `next_symbol=EROK`, `order_boundary=read_only_no_order`, `broker_submit_allowed=false`.
- `/data-health`: rendered `전문 분석 다음 행동`, `전문 분석은 관리 중, 성과 표본 대기`, and `weight 변경 금지`.

## Risks

- This cockpit summarizes existing evidence only. It does not fix source-blocked symbols or create new valuation artifacts.
- EROK remains source-blocked and excluded from professional decision/paper-validation inputs until a periodic filing or dedicated parser exists.
