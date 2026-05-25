# Session Handoff

## Current Status

- 완료: schema foundation, financial metric normalization runner, CLI, local unit/CLI/compile/diff-check verification are implemented.
- 진행 중: AWH verification and EC2 migration/runtime smoke are still pending.
- 첫 수직 슬라이스 구현 완료, 검증 진행 중.
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
  - `financial-metric-normalization-weekly`
  - `pipeline_name=financial_metric_normalization`
  - data-health dataset: `market.financial_metric_normalized`
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

## Exact Next Step

- 다음 세션은 이것부터 시작: Run AWH verification for `professional-equity-analysis-foundation`, then apply the migration on EC2 and execute `financial-metric-normalization-run --execute`.
- Run AWH verification for `professional-equity-analysis-foundation`.
- Then apply migration on EC2, run `financial-metric-normalization-run --execute`, and verify normalized row counts before building peer and valuation snapshots.
