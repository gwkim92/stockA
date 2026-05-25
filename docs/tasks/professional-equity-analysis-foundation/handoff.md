# Session Handoff

## Current Status

- 완료: schema foundation, financial metric normalization runner, CLI, local verification, GitHub push, EC2 migration, EC2 SEC companyfacts seed, EC2 financial metric normalization smoke, and data-health visibility are implemented.
- 진행 중: next task should expand from foundation into peer group and valuation snapshots.
- 첫 수직 슬라이스 구현 완료.
- 이 task는 기존 뉴스·AI·사이클 중심 시스템에 전문가식 주식 분석 레이어를 추가하기 위한 foundation이다.
- 첫 수직 슬라이스는 `financial-metric-normalization-run`이다.

## Implementation Notes

- 추가된 schema:
  - `market.financial_metric_normalized`
  - `ref.peer_group`
  - `ref.peer_group_member`
  - `market.peer_relative_snapshot`
  - `market.valuation_snapshot`
  - `research.equity_research_artifact`
- 추가된 runner:
  - `stockanalysis-operations financial-metric-normalization-run --as-of-date YYYY-MM-DD [--limit N] [--execute]`
  - preview는 read-only다.
  - execute는 `ops.pipeline_run`을 만들고 `market.financial_metric_normalized`만 upsert한다.
  - 추천 score/weight는 변경하지 않는다.
- 추가된 cadence:
  - `sec-companyfacts-weekly`
  - `financial-metric-normalization-weekly`
  - `pipeline_name=sec_companyfacts_upsert`
  - `pipeline_name=financial_metric_normalization`
  - data-health dataset: `market.financial_statement_period`
  - data-health dataset: `market.financial_metric_normalized`
- 추가된 operating-data profile step:
  - `sec-filings-weekly` now runs `sec-filings-weekly`, `sec-companyfacts-weekly`, and `financial-metric-normalization` in order.
- EC2 bug fixes made during live smoke:
  - SEC companyfacts period upsert now dedupes by `instrument_id/statement_scope/period_end`, so point-in-time facts like assets do not conflict with duration facts.
  - SEC companyfacts metric upsert now dedupes by `period_id/metric_code`, so duplicate SEC concepts mapped to the same internal metric do not conflict.
  - SEC companyfacts instrument resolution falls back from company name to known CIK→symbol mapping for AAPL/MSFT/NVDA/TSLA/XOM.
  - financial normalization now selects one prior comparable period via lateral `limit 1`, so restated or duplicate prior periods do not duplicate normalized rows.
- 산출 지표:
  - `revenue_growth_yoy`
  - `gross_margin`
  - `operating_margin`
  - `net_margin`
  - `operating_cash_flow_margin`
  - `free_cash_flow_margin`
  - `cash_flow_quality`
  - `roe`
  - `leverage_ratio`
  - `roic`
- missing input 처리:
  - 계산 가능한 값은 `metric_status='computed'`
  - 입력 fact가 없으면 `metric_status='unavailable'`
  - 과거 비교 기간이 없으면 `metric_status='insufficient_history'`
- SEC companyfacts concept mapping 확장:
  - gross profit, capex, assets, liabilities, shareholders equity를 지원한다.
- 추천 점수 weight는 변경하지 않는다.
- 실거래 broker submit은 계속 제외한다.

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_professional_equity_analysis tests.test_data_operations_cli`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_sec_companyfacts tests.test_professional_equity_analysis tests.test_data_operations_cli`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_sec_companyfacts tests.test_professional_equity_analysis tests.test_data_operations_cli tests.test_data_operations_cadence`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m stockanalysis.operations.cli cadence --cadence weekly | rg 'financial_metric_normalization|financial-metric-normalization'`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m stockanalysis.operations.cli financial-metric-normalization-run --help`
- Passed: `git diff --check`
- Passed: local Docker Postgres migration apply for `db/migrations/0021_professional_equity_analysis.sql`
- Passed: local Docker Postgres dry-run `financial-metric-normalization-run --as-of-date 2026-05-25 --limit 5 --dry-run`
- Passed: local Docker Postgres execute `financial-metric-normalization-run --as-of-date 2026-05-25 --limit 5 --execute`
  - local `run_id`: 151
  - source financial periods in local DB: 0
  - upserted normalized metric rows: 0
- Passed: rollback-scoped local Docker Postgres calculation smoke with temporary instrument `PATST`
  - input: 2024 revenue 1000/net income 100, 2025 revenue 1200/net income 180
  - output: 2024 `net_margin=0.10000000`, `revenue_growth_yoy=insufficient_history`
  - output: 2025 `net_margin=0.15000000`, `revenue_growth_yoy=0.20000000`
  - transaction was rolled back
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests` (`847 tests`)
- Noted: `/opt/homebrew/bin/python3.13 -m unittest discover -s tests` fails because that interpreter does not have `fastapi`; the project verify venv passes.
- Passed: pushed commits through `2ce6d5f` to `origin/codex/local-mvp-runtime-aws-bootstrap`.
- Passed on EC2: code fast-forwarded to `2ce6d5f`.
- Passed on EC2: `db/migrations/0021_professional_equity_analysis.sql` applied.
- Passed on EC2: `sec-companyfacts-upsert` for AAPL, MSFT, NVDA, TSLA, XOM.
  - AAPL run_id `732`, fact_count `1428`, period_count `340`
  - MSFT run_id `733`, fact_count `1435`, period_count `272`
  - NVDA run_id `734`, fact_count `1435`, period_count `324`
  - TSLA run_id `735`, fact_count `1419`, period_count `308`
  - XOM run_id `736`, fact_count `1099`, period_count `298`
- Passed on EC2: `financial-metric-normalization-run --execute`.
  - run_id `738`
  - source_period_count `593`
  - source_instrument_count `5`
  - upserted_count `5930`
  - computed_count `2706`
  - unavailable_count `3133`
  - insufficient_history_count `91`
- Passed on EC2 DB sample:
  - AAPL normalized rows `1280`, computed rows `469`, latest period `2026-03-28`
  - MSFT normalized rows `1280`, computed rows `540`, latest period `2026-03-31`
  - NVDA normalized rows `1260`, computed rows `667`, latest period `2026-04-26`
  - TSLA normalized rows `1180`, computed rows `640`, latest period `2026-03-31`
  - XOM normalized rows `930`, computed rows `390`, latest period `2026-03-31`
- Passed on EC2 API/data-health after service restart:
  - `sec_companyfacts_upsert` job_id `sec-companyfacts-weekly`, latest run `pipeline-run-736`, `health_status=ok`
  - `financial_metric_normalization` job_id `financial-metric-normalization-weekly`, latest run `pipeline-run-738`, `health_status=ok`
  - overall data-health is still `attention_required` because unrelated older market/portfolio runs are stale.

## Follow-up Progress

- `peer-group-and-relative-analysis` was implemented after this foundation task.
  - EC2 run_id `750`
  - `market.peer_relative_snapshot` rows created for the five SEC companyfacts seed instruments.
  - `/api/data-health` shows `peer_relative_analysis` as `health_status=ok`.

## Exact Next Step

- 다음 세션은 이것부터 시작: implement `valuation-snapshot-foundation` using normalized financial metrics, peer relative context, and latest market prices.
- Do not change recommendation weights yet. Fundamental and valuation components remain evidence-only until outcome/eval samples justify calibration.
