# Review

## Review Notes

- schedule runner는 schema 변경 없이 기존 `signal.recommendation_batch`, `signal.recommendation`, `performance.recommendation_outcome` 상태로 due candidate를 계산한다.
- outcome 계산은 기존 `run_performance_outcome_bootstrap`을 재사용한다. 계산 공식 중복은 만들지 않았다.
- OS cron/heartbeat automation은 의도적으로 제외했다. 이번 작업은 automation이 호출할 repo-local runner다.
- `universe_version is not null` batch만 v1 schedule 대상이다. 기존 outcome runner가 `universe_version` identity를 요구하기 때문이다.

## Verification Evidence

- `python3 -m compileall src tests`: 통과
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`: 205 tests 통과
- `bash -n scripts/verify_scheduled_outcome_runner.sh`: 통과
- `bash scripts/verify_scheduled_outcome_runner.sh`: 통과
  - Docker Postgres migration/seed 적용 통과
  - schedule CLI로 `performance.recommendation_outcome` 2건 확인
  - schedule CLI로 `performance.thesis_outcome` 2건 확인
  - 2024-11-04 AAPL alpha `0.005000` 확인
  - 2024-12-02 AAPL alpha `0.060000` 확인
  - child `performance_outcome_bootstrap` succeeded source run link 2건 확인
  - parent `performance_outcome_schedule_bootstrap` latest status `succeeded` 확인
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task scheduled-outcome-runner`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음
