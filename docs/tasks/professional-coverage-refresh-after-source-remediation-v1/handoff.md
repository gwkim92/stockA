# professional-coverage-refresh-after-source-remediation-v1 Handoff

## Status

- completed: EC2 professional coverage refresh, post-decision refresh, recommendation component rerun, quality eval, API source blocker exposure, frontend source blocker rendering, and route smoke are complete.

## Context

- `segment-history-source-linkage-remediation-v1` completed with EC2 coverage run `1452`.
- Clean source states now include AAPL/DIS/FANG/GILD `trend_backed`, ADI/AEIS/ALAB/ARM/ELF `single_reportable_segment_no_disaggregated_segment_table`, and EROK `sec_companyfacts_missing_us_gaap_facts`.
- ARM polluted segment labels were removed from `research.segment_footnote_evidence`.
- This task refreshed downstream professional coverage and exposed source blockers in stock/recommendation DTOs and UI.
- EC2 evidence:
  - coverage refresh `run_id=1519`, status `completed_with_failures`; failures were precise source blockers for EROK (`facts.us-gaap` absent) and SPY (`companyfacts` 404 fund-like product).
  - post-decision refresh `run_id=1565`, status `completed_with_failures`; BE/AVGO/DG/GOOG coverage refreshed while EROK/SPY remained precise blockers.
  - recommendation components rerun `run_id=1579`, status `completed`.
  - quality eval `run_id=1580`, `eval_run_id=25`, `quality_status=ready_for_weight_review`, professional coverage `39/45 = 0.866667`, outcome count `30`.
  - route smoke confirmed `/stocks/SPY` and `/recommendations/recommendation-157` show `fund_company_financial_model_not_applicable`, `/stocks/EROK` shows SEC companyfacts source blocker, `/stocks/ARM` shows available financial model and no polluted segment labels.

## Exact Next Step

- exact next step: start `portfolio-and-fund-instrument-analysis-v1`, because SPY is not a company and must be analyzed through holdings, benchmark composition, tracking error, exposure, expense ratio, liquidity, and portfolio role rather than a company financial statement model.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not synthesize segment rows for single-segment companies.
- Do not force ETF/fund-like instruments into company financial models.
