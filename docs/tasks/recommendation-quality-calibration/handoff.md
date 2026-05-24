# Session Handoff

## Current Status

- 완료:
  - task contract를 만들었다.
  - 기존 추천 score component와 performance outcome 구조를 확인했다.
  - `src/stockanalysis/operations/recommendation_quality_eval.py`에 read-only eval SQL, scoring, `ai.eval_run` 저장 runner를 추가했다.
  - `stockanalysis-operations recommendation-quality-eval-run` CLI를 추가했다.
  - `decision-daily` profile에 paper validation 이후 recommendation quality eval step을 추가했다.
  - cadence registry에 `recommendation-quality-eval-daily`를 추가했다.
  - 기존 `cycle_score`와 이미 허용된 `macro_flow_score`를 zero-weight guardrail에서 제외해 오탐을 막았다.
  - 추천 산식과 score weight는 변경하지 않았다.
  - EC2에 배포하고 실제 DB 기준 `--execute` smoke를 실행했다.

## EC2 Smoke Result

- 명령: `stockanalysis-operations recommendation-quality-eval-run --env-file /opt/stockanalysis/runtime/data-operations.env --as-of-date 2026-05-24 --horizon 30d --min-sample-size 20 --execute`
- 결과:
  - `run_id`: 705
  - `eval_run_id`: 3
  - `quality_status`: `needs_more_data`
  - `sample_status`: `insufficient_sample`
  - `recommendation_count`: 30
  - `outcome_count`: 0
  - protected cycle guardrail: 55/55 rows have zero weight, `cycle_weight_unchanged=true`
  - latest paper validation: `failed`, `conflict_count=3`
- 해석:
  - runner와 저장 경로는 정상 동작한다.
  - outcome 표본이 아직 없으므로 추천 weight 변경은 금지 상태가 맞다.
  - paper validation conflict가 남아 있어 다음 UX에서 페이퍼 상태를 더 명확히 보여줘야 한다.

## Verification

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_recommendation_quality_eval tests.test_data_operations_cli tests.test_operating_data_orchestrator tests.test_data_operations_cadence`: passed, 68 tests.
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`: passed.
- `git diff --check`: passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-quality-calibration`: passed.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`: passed, 834 tests.
- EC2 `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_recommendation_quality_eval tests.test_data_operations_cli tests.test_operating_data_orchestrator tests.test_data_operations_cadence`: passed, 68 tests.
- EC2 `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m compileall -q src tests`: passed.

## Exact Next Step

- exact next step: `decision-cockpit-ux-v2`를 시작한다. 홈, `/data-health`, `/intelligence`, `/cycle-map`, `/paper-trading`을 "오늘 무엇을 봐야 하는가"와 "수집→AI해석→전파→추천/페이퍼 검증" 흐름으로 재정리한다.
- 추천 산식 weight 변경은 충분한 `performance.recommendation_outcome` 표본이 쌓이고 별도 calibration 승인 task가 열리기 전까지 하지 않는다.
