# Task Review

## Summary

- `operating-data-run`을 자동 운영 profile 단위로 분리했다.
- 하나의 전체 runner는 제거하지 않고 `full-recovery`로 명시해 수동 복구와 배포 smoke에만 쓰도록 의미를 분리했다.
- 주기별 자동화 후보는 `news-intraday`, `market-daily`, `decision-daily`, `macro-weekly`, `performance-monthly`다.

## Verification Evidence

- Focused tests passed:
  - `tests.test_operating_data_orchestrator`
  - `tests.test_data_operations_cli`
  - `tests.test_data_operations_cadence`

## Remaining Risks

- 실제 EC2 recurring scheduler deployment는 다음 작업이다.
- 이 작업은 실행 단위 분리이며, 유료 provider나 실거래 broker flow를 추가하지 않는다.
