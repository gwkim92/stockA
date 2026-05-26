# professional-source-blocker-raw-filing-remediation-v1 Handoff

## Status

- in progress: this task is defined and ready to start as the immediate next task after `professional-source-gap-remediation-decision-v1`.

## Context

- EC2 `professional-source-gap-remediation-decision-v1` completed on commit `7b8fe1a`.
- Decision runner `run_id=1599`, `eval_run_id=29` classified `EROK` as `non_remediable_current_free_public_data`.
- GOOG was remediated by adding SEC shares concept mappings, rerunning companyfacts `run_id=1601`, and rerunning SOTP `run_id=1602`.
- Latest EC2 `/api/data-health` source gaps: `gap_count=2`, `source_blocker_count=1`, `coverage_gap_count=0`, `fund_not_applicable_count=1`, symbols `EROK:source_blocker`, `SPY:fund_not_applicable`.

## Exact Next Step

- exact next step: inspect EROK free-public raw SEC filing/XBRL feasibility. If the source has usable financial facts, add a backend parser/runner path; otherwise persist a durable exclusion/blocker decision that prevents fake remediation.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not fabricate missing financial facts.
- Do not convert SPY/ETF fund-not-applicable cases into company-financial failures.
