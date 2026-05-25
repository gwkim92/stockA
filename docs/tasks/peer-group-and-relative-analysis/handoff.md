# Session Handoff

## Current Status

- 완료: peer-relative runner, CLI, cadence, operating-data profile, unit/CLI/orchestrator tests, and local Postgres rollback smoke are implemented.
- 진행 중: GitHub push and EC2 runtime smoke are still pending.

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

## Exact Next Step

- 다음 세션은 이것부터 시작: commit/push, deploy to EC2, run `peer-relative-analysis-run --execute`, then verify `/api/data-health` shows `peer_relative_analysis` with `health_status=ok`.
