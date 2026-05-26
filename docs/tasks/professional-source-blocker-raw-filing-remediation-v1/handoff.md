# professional-source-blocker-raw-filing-remediation-v1 Handoff

## Status

- completed: local implementation, EC2 deploy, live runner execution, and route/data-health smoke passed.

## Context

- EC2 `professional-source-gap-remediation-decision-v1` completed on commit `7b8fe1a`.
- Decision runner `run_id=1599`, `eval_run_id=29` classified `EROK` as `non_remediable_current_free_public_data`.
- GOOG was remediated by adding SEC shares concept mappings, rerunning companyfacts `run_id=1601`, and rerunning SOTP `run_id=1602`.
- Latest EC2 `/api/data-health` source gaps: `gap_count=2`, `source_blocker_count=1`, `coverage_gap_count=0`, `fund_not_applicable_count=1`, symbols `EROK:source_blocker`, `SPY:fund_not_applicable`.
- EC2 raw filing remediation runner completed on commit `9ff096f` with `run_id=1607`, `eval_run_id=30`.
- EROK companyfacts namespaces are `ffd` only; `facts.us-gaap` is absent.
- EROK SEC submissions include `S-8`, `S-1/S-1/A`, and `424B4`; supported periodic filings `10-K/10-Q/20-F/40-F` count is `0`.
- Latest prospectus source is `424B4`, filed `2026-05-14`.
- Decision is `durable_exclusion_until_periodic_filing` with blocker `ipo_prospectus_without_standard_periodic_financials`.

## Exact Next Step

- exact next step: move to `news-intraday-scheduler-failure-remediation-v1`, because the EC2 profile scheduler is installed but the last `news-intraday` service result is `exit-code`.

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
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_sec_companyfacts tests.test_professional_source_gap_remediation_decision tests.test_professional_source_blocker_raw_filing_remediation tests.test_frontend_live_adapter`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task professional-source-blocker-raw-filing-remediation-v1`

## EC2 Verification

- Deployed commit: `9ff096f`.
- Runner: `/opt/stockanalysis/venv/bin/python -m stockanalysis.operations.cli professional-source-blocker-raw-filing-remediation-run --env-file /opt/stockanalysis/runtime/data-operations.env --as-of-date 2026-05-26 --cik 0002104882 --fallback-symbol EROK --max-filings 50 --execute`.
- Output artifact: `/opt/stockanalysis/runtime/professional-source-blocker-raw-filing-remediation-2026-05-26.json`.
- Result: `run_id=1607`, `eval_run_id=30`, `decision_status=durable_exclusion_until_periodic_filing`, `blocker_code=ipo_prospectus_without_standard_periodic_financials`, `durable_exclusion=true`.
- `/api/data-health` now exposes `raw_filing_decision.eval_run_id=eval-run-30`, `raw_filing_decision.status=durable_exclusion_until_periodic_filing`, `latest_prospectus_form_type=424B4`, `latest_prospectus_filing_date=2026-05-14`.
- Route smoke: `/`, `/data-health`, `/stocks/EROK` returned `200`.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not fabricate missing financial facts.
- Do not convert SPY/ETF fund-not-applicable cases into company-financial failures.
