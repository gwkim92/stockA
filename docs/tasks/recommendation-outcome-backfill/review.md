# Review

## Result

- 로컬 구현과 검증 완료.
- 새 CLI: `stockanalysis-operations recommendation-outcome-backfill-run --due-on-date YYYY-MM-DD --horizon-day 30`
- 저장 경로:
  - `performance.recommendation_outcome`
  - `performance.thesis_outcome`
  - `ops.pipeline_run.pipeline_name='performance_outcome_schedule_bootstrap'`
- `decision-daily` profile은 `recommendation-quality-eval` 전에 `recommendation-outcome-backfill`을 먼저 실행한다.
- `performance-outcome-monthly`는 기존 ingest CLI 직접 호출 대신 operations CLI wrapper를 사용한다.
- 추천 산식과 score weight는 변경하지 않았다.

## Expected Runtime Behavior

- preview:
  - due recommendation batch와 missing outcome count만 보고한다.
  - DB write를 하지 않는다.
- execute:
  - 기존 `performance_outcome_schedule_bootstrap` 경로를 호출한다.
  - `performance.recommendation_outcome`, `performance.thesis_outcome`을 idempotent upsert한다.
  - `ops.pipeline_run`에 성공/실패를 남긴다.

## Remaining Risk

- 실제 outcome 표본은 추천일 이후 horizon이 지난 batch와 해당 기간 가격 데이터가 있어야 생긴다.
- EC2 SSH 접근이 현재 timeout이면 원격 smoke는 별도 네트워크/IP 허용 후 진행해야 한다.

## Verification

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_recommendation_outcome_backfill`: passed, 3 tests.
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_data_operations_cli tests.test_operating_data_orchestrator tests.test_data_operations_cadence`: passed, 62 tests.
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`: passed.
- `git diff --check`: passed.
