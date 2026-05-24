# Session Handoff

## Current Status

- 진행 중:
  - `recommendation-outcome-backfill` task contract를 만들었다.
  - 기존 `stockanalysis.performance.outcome`이 가격 기반 outcome upsert를 이미 제공하는 것을 확인했다.
  - 새 operations wrapper `run_recommendation_outcome_backfill`을 추가했다.
  - 새 CLI `stockanalysis-operations recommendation-outcome-backfill-run`을 추가했다.
  - `decision-daily` profile에서 `recommendation-quality-eval` 전에 `recommendation-outcome-backfill`을 실행하도록 연결했다.
  - `performance-outcome-monthly`도 shell/ingest 직접 경로 대신 operations CLI wrapper를 사용하도록 바꿨다.
  - cadence registry에 `recommendation-outcome-backfill-daily`를 추가했다.

## Data Policy

- outcome은 실제 `market.daily_price_bar`의 entry/exit/min price와 benchmark price만 사용한다.
- due candidate가 없거나 가격 데이터가 부족하면 가짜 수익률을 만들지 않는다.
- 추천 산식과 score weight는 변경하지 않는다.

## Verification

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_recommendation_outcome_backfill`: passed, 3 tests.
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_data_operations_cli tests.test_operating_data_orchestrator tests.test_data_operations_cadence`: passed, 62 tests.
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`: passed.
- `git diff --check`: passed.
- 첫 `awh verify`는 handoff의 exact next step 문구 형식 누락으로 실패했다. 기능/코드 실패는 아니다.

## Exact Next Step

- exact next step: `recommendation-outcome-backfill` 변경을 커밋/푸시하고, EC2 SSH 접근이 복구되면 `recommendation-outcome-backfill-run --env-file /opt/stockanalysis/runtime/data-operations.env --due-on-date 2026-05-24 --horizon-day 30 --execute` smoke를 실행한다.
