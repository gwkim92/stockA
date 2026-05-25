# Session Handoff

## Current Status

- 진행 중: local implementation, unit verification, and EC2 rollback SQL smoke are done; commit/push and EC2 execute are next.

## Implementation Notes

- 이번 task는 기존 recommendation bootstrap total score를 건드리지 않는 보강 runner로 구현한다.
- 추가된 CLI:
  - `stockanalysis-operations recommendation-fundamental-components-run --as-of-date YYYY-MM-DD --execute`
- 추가된 cadence:
  - `recommendation-fundamental-components-daily`
  - `pipeline_name=recommendation_fundamental_components`
  - data-health dataset: `signal.recommendation_score_component`
- 추가된 operating-data profile step:
  - `decision-daily` now runs `recommendation-fundamental-components` after `recommendation-bootstrap`.
- 대상 component:
  - `fundamental_quality_score`
  - `valuation_margin_score`
  - `peer_relative_score`
  - `balance_sheet_risk_penalty`
  - `thesis_consistency_score`
- 기본 weight는 전부 `0.0000`.
- `--as-of-date` 기준 최신 재무/피어/밸류에이션을 읽고, selected recommendation batch는 해당 날짜 이하 최신 batch를 선택한다.

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_recommendation_fundamental_components tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m stockanalysis.operations.cli recommendation-fundamental-components-run --help`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- Passed: `git diff --check`
- Passed: EC2 rollback SQL smoke before deployment:
  - preview: selected batch `13`, selected batch date `2026-05-23`, active recommendations `5`
  - coverage: financial `1`, peer `1`, valuation `1`, linked thesis `5`
  - rollback upsert: component_count `25`, non_zero_weight_count `0`, recommendation_total_score_mutated `false`
- Pending: AWH verify after final doc update.
- Pending: EC2 execute smoke after commit/push.

## Exact Next Step

- 다음 세션은 이것부터 시작: run AWH verify, commit/push, pull on EC2, execute `recommendation-fundamental-components-run --as-of-date 2026-05-25 --execute`, restart services, then confirm data-health tracks `recommendation_fundamental_components`.
