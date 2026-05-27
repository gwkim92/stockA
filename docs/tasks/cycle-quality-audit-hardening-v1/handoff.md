# cycle-quality-audit-hardening-v1 Handoff

## Status

- status: implemented_pending_ec2_smoke
- started_at: 2026-05-27
- current status: implemented locally and pending EC2 deploy/smoke.
- completed: audit SQL now emits detailed contamination and normal macro-flow samples.
- completed: `/data-health` renders audit sample groups in Korean.
- completed: targeted backend tests, compileall, Next typecheck/build, AWH verify, and diff check.

## Current Decision

- Reuse the existing `cycle-ai-quality-audit-run` instead of adding a new scheduler or table.
- Treat `normal_macro_flows` as a positive control: macro/theme news without direct ticker can be correct and should be visible as normal, not hidden as a missing-symbol error.
- Keep cleanup as a separate explicit runner. This task does not delete rows.

## Next Step

- exact next step: deploy to EC2, run `cycle-ai-quality-audit-run --execute`, confirm `/api/data-health` and `/data-health` expose the richer audit samples, then update this handoff with smoke evidence.

## Verification So Far

- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_cycle_ai_quality_audit tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task cycle-quality-audit-hardening-v1`
- passed: `git diff --check`
- pending: EC2 smoke.

## Risks

- Audit samples depend on current event/document linkage quality. If a source event has multiple linked documents, a sample title may represent one source document from the event group.
- This task does not decide whether an alert should page the operator. Alert routing remains handled by `alert-destination-free-channel-v1`.
