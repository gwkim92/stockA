# professional-source-blocker-raw-filing-remediation-v1 Handoff

## Status

- in progress: local implementation is complete and verified; EC2 deploy and live execute smoke are next.

## Context

- EC2 `professional-source-gap-remediation-decision-v1` completed on commit `7b8fe1a`.
- Decision runner `run_id=1599`, `eval_run_id=29` classified `EROK` as `non_remediable_current_free_public_data`.
- GOOG was remediated by adding SEC shares concept mappings, rerunning companyfacts `run_id=1601`, and rerunning SOTP `run_id=1602`.
- Latest EC2 `/api/data-health` source gaps: `gap_count=2`, `source_blocker_count=1`, `coverage_gap_count=0`, `fund_not_applicable_count=1`, symbols `EROK:source_blocker`, `SPY:fund_not_applicable`.

## Exact Next Step

- exact next step: deploy the local implementation to EC2, run `professional-source-blocker-raw-filing-remediation-run` for `EROK`/CIK `0002104882`, restart read-only services, and confirm `/api/data-health` shows the raw filing durable exclusion metadata.

## Implementation Notes

- Added `src/stockanalysis/operations/professional_source_blocker_raw_filing_remediation.py`.
- Added CLI: `stockanalysis-operations professional-source-blocker-raw-filing-remediation-run`.
- The runner reads free SEC submissions and companyfacts, then classifies the blocker as:
  - `standard_companyfacts_available` when `facts.us-gaap` exists,
  - `periodic_raw_xbrl_candidate` when supported 10-K/10-Q/20-F/40-F XBRL exists,
  - `durable_exclusion_until_periodic_filing` when only prospectus/registration sources are available,
  - `durable_exclusion_no_supported_public_financial_filing` when no usable public filing exists.
- The runner records the decision in `ai.eval_run` and `ops.pipeline_run`; it does not write financial facts.
- `/api/data-health` now reads latest `professional_source_blocker_raw_filing_remediation` eval output and exposes `raw_filing_decision` inside each professional source gap row.

## Local Verification So Far

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_professional_source_blocker_raw_filing_remediation tests.test_data_operations_cli tests.test_frontend_live_adapter`
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not fabricate missing financial facts.
- Do not convert SPY/ETF fund-not-applicable cases into company-financial failures.
