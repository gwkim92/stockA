# source-blocked-recommendation-guardrail-v1 Handoff

## Status

- in progress: recommendation/stock DTOs now expose `professional_source_guardrail`, and source-blocked operating-company recommendation detail is hard-blocked in evidence review and professional decision waterfall.
- in progress: local verification passed; EC2 deploy/smoke is the remaining step.
- blockers: none known.

## Context

- `cycle-ai-quality-audit-contamination-remediation-v1` completed on EC2: latest audit `run_id=1623`, `audit_status=ok`, `issue_count=0`, `audit_score=100`.
- `/api/data-health` still reports `professional_source_gap_attention`.
- EROK is an operating company with `active_recommendation_count=1`, but `professional-source-blocker-raw-filing-remediation-v1` classified it as `durable_exclusion_until_periodic_filing`.
- The current system should not present such recommendations as professionally usable until supported periodic financial data or a safe parser exists.

## Exact Next Step

- exact next step: deploy the current branch to EC2, restart FastAPI/Next.js, and verify `/api/recommendations/recommendation-67`, `/api/data-health`, `/recommendations/recommendation-67`, and `/data-health`.

## Implementation Notes

- `src/stockanalysis/frontend/live_adapter.py` adds `professional_source_guardrail`.
- `sec_companyfacts_missing_us_gaap_facts`, `sec_companyfacts_not_found`, and `financial_source_linkage_failed` block professional use for operating companies, but ETF/fund `fund_company_financial_model_not_applicable` remains a separate fund-analysis boundary.
- Recommendation evidence review gets a `professional_source_data` blocked gate only when a source blocker exists.
- Recommendation professional waterfall gets `status=source_data_blocked`, an explicit `source_data_guardrail` step, `paper_validation_input_allowed=false`, and blocked tones for financial quality and paper validation.
- `/api/data-health` source gaps now expose `guarded_source_blocked_recommendation_count` and per-gap `active_recommendation_professional_use_blocked`.
- Frontend recommendation detail and data-health labels now show the Korean source-blocked state.

## Local Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter tests.test_data_operations_cli`
- Passed: `cd apps/web && npm run typecheck`
- Passed: `cd apps/web && npm run build`
- Passed: `bash scripts/verify_project_execution_roadmap.sh`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task source-blocked-recommendation-guardrail-v1`

## Guardrails

- Keep recommendation scoring weights unchanged.
- Keep broker/order flow read-only.
- Do not delete historical recommendation records.
- Do not fabricate missing EROK financial facts.
