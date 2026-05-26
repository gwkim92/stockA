# segment-history-source-linkage-remediation-v1 Review

## Review Summary

- Completed. The remaining source truth blockers from the 10-symbol segment coverage sample are no longer ambiguous: ARM is supported as a 20-F annual companyfacts issuer and EROK is explicitly blocked by missing SEC financial statement facts.

## Issues Found

- ARM was a foreign private issuer with Form `20-F` annual facts. The previous companyfacts normalizer only accepted `10-K`/`10-Q`, so it skipped usable ARM financial facts.
- ARM raw 20-F also exposed segment parser contamination: consolidated expense labels such as `Operating expenses` and `Non-staff costs` were previously parsed as segments. The parser now skips single segment summary tables, excludes financial statement labels, and cleans stale reported segment rows for skipped candidates.
- EROK has SEC companyfacts taxonomy `ffd` only and no `facts.us-gaap`; the system now classifies this as `sec_companyfacts_missing_us_gaap_facts`.

## Residual Risks

- EROK may become supported later if SEC publishes annual financial facts. Until then it should remain a precise source blocker, not a parser failure.
- ARM has no disaggregated operating segment table, so it correctly remains a single segment/no-detail case rather than synthetic SOTP segment input.

## Verification Evidence

- Local: `PYTHONPATH=src python3 -m unittest tests.test_sec_companyfacts tests.test_financial_period_source_linkage tests.test_segment_history_coverage_expansion` -> passed before EC2 smoke.
- Local: `PYTHONPATH=src python3 -m unittest tests.test_segment_history_coverage_expansion tests.test_professional_equity_analysis tests.test_sec_companyfacts tests.test_financial_period_source_linkage` -> `Ran 62 tests OK`.
- Local: `PYTHONPATH=src python3 -m compileall -q src tests` -> passed.
- Local: `git diff --check` -> passed.
- EC2: focused tests passed after deploying commits `e5bec53`, `5d025d1`, `bd3f2ef`, and `68928c8`.
- EC2 source linkage: `financial-period-source-linkage-arm-20f.json`, `run_id=1339`, `companyfacts_report.fact_count=54`, `period_count=8`, `raw_fetch_success_count=2`.
- EC2 ARM cleanup smoke: `run_id=1416`, ARM `coverage_status=single_reportable_segment_no_disaggregated_segment_table`, `arm_reported_segment_metric_count=0`, `unsupported_layout_count=0`.
- EC2 10-symbol smoke: `run_id=1452`, status `completed_with_failures` only because EROK has no financial facts, status counts `trend_backed=4`, `single_reportable_segment_no_disaggregated_segment_table=5`, `sec_companyfacts_missing_us_gaap_facts=1`, `unsupported_layout_count=0`, `recommendation_scoring_mutated=false`, `automatic_order_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`.
