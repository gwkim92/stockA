# source-blocked-recommendation-guardrail-v1 Handoff

## Status

- in progress: task contract and plan are created; implementation has not begun.
- blockers: none known yet.

## Context

- `cycle-ai-quality-audit-contamination-remediation-v1` completed on EC2: latest audit `run_id=1623`, `audit_status=ok`, `issue_count=0`, `audit_score=100`.
- `/api/data-health` still reports `professional_source_gap_attention`.
- EROK is an operating company with `active_recommendation_count=1`, but `professional-source-blocker-raw-filing-remediation-v1` classified it as `durable_exclusion_until_periodic_filing`.
- The current system should not present such recommendations as professionally usable until supported periodic financial data or a safe parser exists.

## Exact Next Step

- exact next step: trace the EROK recommendation detail DTO and score/professional decision waterfall to find where source blocker status should become a hard professional-use block without changing score weights.

## Guardrails

- Keep recommendation scoring weights unchanged.
- Keep broker/order flow read-only.
- Do not delete historical recommendation records.
- Do not fabricate missing EROK financial facts.
