# Session Handoff

## Current Status

- 완료: peer-relative runner, CLI, cadence, operating-data profile, local tests, local Postgres rollback smoke, GitHub push, EC2 execution, and data-health visibility are implemented.
- 진행 중: next task should expand into valuation snapshot foundation.

## Implementation Notes

- 입력:
  - `market.financial_metric_normalized`
  - `ref.instrument_classification_membership`
  - `ref.classification_node`
- 출력:
  - `ref.peer_group`
  - `ref.peer_group_member`
  - `market.peer_relative_snapshot`
- 기본 정책:
  - default statement scope는 `annual`.
  - classification membership 기반 그룹이 있으면 사용한다.
  - 항상 `US_CORE_FINANCIAL_DISCLOSURE` fallback group을 만든다.
  - `min-peer-count` 미만이면 percentile 대신 `insufficient_data`를 남긴다.
  - recommendation score/weight는 변경하지 않는다.
- 추가된 CLI:
  - `stockanalysis-operations peer-relative-analysis-run --as-of-date YYYY-MM-DD --execute`
- 추가된 cadence:
  - `peer-relative-analysis-weekly`
  - `pipeline_name=peer_relative_analysis`
  - data-health dataset: `market.peer_relative_snapshot`
- 추가된 operating-data profile step:
  - `sec-filings-weekly` now runs `peer-relative-analysis` after `financial-metric-normalization`.

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_professional_equity_analysis tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m stockanalysis.operations.cli peer-relative-analysis-run --help`
- Passed: `git diff --check`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task peer-group-and-relative-analysis`
- Passed: rollback-scoped local Docker Postgres peer relative smoke with temporary instruments `PRA`, `PRB`, `PRC`.
  - output group count `2`
  - snapshot count `60`
  - `PRA` net margin/revenue growth ranked `below_peer`
  - `PRB` net margin/revenue growth ranked `near_peer`
  - `PRC` net margin/revenue growth ranked `above_peer`
  - transaction was rolled back
- Passed: pushed commit `62ae997` to `origin/codex/local-mvp-runtime-aws-bootstrap`.
- Passed on EC2: code fast-forwarded to `62ae997`.
- Passed on EC2: `peer-relative-analysis-run --as-of-date 2026-05-25 --statement-scope annual --execute`.
  - run_id `750`
  - coverage_instrument_count `5`
  - latest_metric_count `43`
  - classification_peer_group_count `1`
  - peer_group_count `2`
  - peer_member_count `8`
  - snapshot_count `80`
  - relative_signal_counts: `above_peer=27`, `below_peer=27`, `near_peer=16`, `insufficient_data=10`
- Passed on EC2 DB sample:
  - `US_CORE_FINANCIAL_DISCLOSURE` has `5` members and `250` snapshots.
  - `CLASSIFICATION_INTERNAL_THEME_SUBTHEME_US_MARKET_BREADTH` has `3` members and `90` snapshots.
  - fallback group examples:
    - `net_margin`: TSLA/XOM below peer, AAPL near peer, MSFT/NVDA above peer.
    - `revenue_growth_yoy`: AAPL/XOM below peer, MSFT near peer, TSLA/NVDA above peer.
    - `free_cash_flow_margin`: TSLA/XOM below peer, NVDA near peer, AAPL/MSFT above peer.
- Passed on EC2 API/data-health after service restart:
  - `peer_relative_analysis` job_id `peer-relative-analysis-weekly`, latest run `pipeline-run-750`, `health_status=ok`
  - overall data-health remains `attention_required` because unrelated older market/portfolio jobs are stale.

## Exact Next Step

- 다음 세션은 이것부터 시작: implement `valuation-snapshot-foundation` using `market.valuation_snapshot`, latest market price, normalized FCF/margins, and peer relative context. Keep recommendation weights unchanged.
