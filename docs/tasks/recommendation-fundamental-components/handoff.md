# Session Handoff

## Current Status

- 완료: backend runner, CLI, cadence, operating-data profile, local verification, GitHub push, EC2 execution, DB sample, and data-health visibility are implemented.

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
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-fundamental-components`
- Passed: EC2 rollback SQL smoke before deployment:
  - preview: selected batch `13`, selected batch date `2026-05-23`, active recommendations `5`
  - coverage: financial `1`, peer `1`, valuation `1`, linked thesis `5`
  - rollback upsert: component_count `25`, non_zero_weight_count `0`, recommendation_total_score_mutated `false`
- Passed: pushed commit `1e8bb04` to `origin/codex/local-mvp-runtime-aws-bootstrap`.
- Passed on EC2: code fast-forwarded to `1e8bb04`.
- Passed on EC2: `recommendation-fundamental-components-run --as-of-date 2026-05-25 --market-code US --strategy-name long_term_core --horizon-type long_term --execute`.
  - run_id `760`
  - selected_batch_id `13`
  - selected_batch_as_of_date `2026-05-23`
  - active_recommendation_count `5`
  - financial_coverage_count `1`
  - peer_coverage_count `1`
  - valuation_coverage_count `1`
  - component_count `25`
  - non_zero_weight_count `0`
  - recommendation_total_score_mutated `false`
- Passed on EC2 DB sample:
  - `balance_sheet_risk_penalty`: 5 rows, min/max weight `0.0000`, avg score `0.6000`
  - `fundamental_quality_score`: 5 rows, min/max weight `0.0000`, avg score `0.5350`
  - `peer_relative_score`: 5 rows, min/max weight `0.0000`, avg score `0.5350`
  - `thesis_consistency_score`: 5 rows, min/max weight `0.0000`, avg score `0.7500`
  - `valuation_margin_score`: 5 rows, min/max weight `0.0000`, avg score `0.4798`
- Passed on EC2 API/data-health after service restart:
  - `recommendation_fundamental_components` job_id `recommendation-fundamental-components-daily`, latest run `pipeline-run-760`, `health_status=ok`.

## Exact Next Step

- 다음 세션은 이것부터 시작: expand recommendation/detail frontend and API copy so the new zero-weight fundamental components are shown as separate 재무/피어/밸류에이션/thesis evidence, then continue toward `ai-equity-research-reporting` or `portfolio-risk-budget` depending on roadmap priority.
