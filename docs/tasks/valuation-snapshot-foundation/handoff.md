# Session Handoff

## Current Status

- 완료: local implementation, unit verification, GitHub push, EC2 execution, DB sample, and data-health visibility are implemented.

## Implementation Notes

- 입력:
  - `market.daily_price_bar`
  - `market.financial_statement_period`
  - `market.financial_metric_value`
  - `market.financial_metric_normalized`
  - `market.peer_relative_snapshot`
- 출력:
  - `market.valuation_snapshot`
- 추가된 SEC companyfacts metric:
  - `shares_outstanding` from `facts.dei.EntityCommonStockSharesOutstanding` with `shares` unit.
- 추가된 CLI:
  - `stockanalysis-operations valuation-snapshot-run --as-of-date YYYY-MM-DD --statement-scope annual --execute`
- 추가된 cadence:
  - `valuation-snapshot-weekly`
  - `pipeline_name=valuation_snapshot`
  - data-health dataset: `market.valuation_snapshot`
- 추가된 operating-data profile step:
  - `sec-filings-weekly` now runs `valuation-snapshot` after `peer-relative-analysis`.

## Design Notes

- EC2에서 AAPL, MSFT, NVDA, TSLA, XOM의 `market.daily_price_bar.market_cap`은 non-null rows가 0건이었다. 따라서 이 작업은 market cap을 추정하지 않는다.
- `dcf_lite`는 positive free cash flow와 positive `shares_outstanding`가 있을 때만 생성한다.
- `relative_multiple`과 `scenario_range`는 current-price anchored range이며 absolute intrinsic valuation claim이 아니다.
- Recommendation score/weight는 변경하지 않는다.

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_sec_companyfacts tests.test_professional_equity_analysis tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m stockanalysis.operations.cli valuation-snapshot-run --help`
- Passed: `git diff --check`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task valuation-snapshot-foundation`
- Passed on EC2 rollback SQL smoke before deployment:
  - preview: `price_coverage_count=26`, `raw_financial_input_count=5`, `normalized_input_count=5`, `peer_context_count=5`, `valuation_context_count=5`, `dcf_lite_eligible_count=0`, `existing_valuation_count=0`
  - rollback upsert: `snapshot_count=10`, method counts `relative_multiple=5`, `scenario_range=5`
- Passed: pushed commit `1273e9b` to `origin/codex/local-mvp-runtime-aws-bootstrap`.
- Passed on EC2: code fast-forwarded to `1273e9b`, then `604f342` for lower DCF-lite confidence.
- Passed on EC2: re-ran SEC companyfacts for core filers and loaded `shares_outstanding`.
  - AAPL run_id `751`, fact_count `1496`
  - MSFT run_id `752`, fact_count `1502`
  - NVDA run_id `753`, fact_count `1503`
  - TSLA run_id `754`, fact_count `1479`
  - XOM run_id `755`, fact_count `1167`
- Passed on EC2: `financial-metric-normalization-run --as-of-date 2026-05-25 --execute`.
  - run_id `756`
  - upserted_count `8720`
  - computed_count `2454`
- Passed on EC2: `peer-relative-analysis-run --as-of-date 2026-05-25 --statement-scope annual --execute`.
  - run_id `757`
  - peer_group_count `2`
  - snapshot_count `80`
- Passed on EC2: `valuation-snapshot-run --as-of-date 2026-05-25 --statement-scope annual --execute`.
  - run_id `759`
  - valuation_context_count `5`
  - dcf_lite_eligible_count `5`
  - snapshot_count `15`
  - method_counts: `dcf_lite=5`, `relative_multiple=5`, `scenario_range=5`
  - confidence_summary: `min=0.35`, `avg=0.40`, `max=0.45`
- Passed on EC2 DB sample:
  - 5 symbols have valuation snapshots: AAPL, MSFT, NVDA, TSLA, XOM.
  - DCF-lite confidence is `0.3500`, relative multiple is `0.4500`, scenario range is `0.4000`.
- Passed on EC2 API/data-health after service restart:
  - `valuation_snapshot` job_id `valuation-snapshot-weekly`, latest run `pipeline-run-759`, `health_status=ok`.
  - `sec_companyfacts_upsert`, `financial_metric_normalization`, and `peer_relative_analysis` are also `health_status=ok`.

## Exact Next Step

- 다음 세션은 이것부터 시작: implement `recommendation-fundamental-components` as zero-weight score components that read financial quality, peer relative, and valuation snapshots without changing recommendation totals.
