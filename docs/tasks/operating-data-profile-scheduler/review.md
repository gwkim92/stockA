# Task Review

## Summary

- `operating-data-run`을 자동 운영 profile 단위로 분리했다.
- 하나의 전체 runner는 제거하지 않고 `full-recovery`로 명시해 수동 복구와 배포 smoke에만 쓰도록 의미를 분리했다.
- 주기별 자동화 후보는 `news-intraday`, `market-daily`, `decision-daily`, `macro-weekly`, `performance-monthly`다.
- 추가로 profile별 운영 scheduler invocation packet 생성을 위한 `operating-data-profile-scheduler-invocation-plan` CLI 커맨드를 연결했고,
  `stockanalysis-operations`가 target/platform/출력 경로/일정 정책을 repo-outside 기준으로 검증한 뒤 profile별 `stockanalysis.operations.cli operating-data-run` preview command를 렌더하도록 마무리했다.
- `full-recovery`는 기본 profile 후보에서 제외되며 필요 시 `--include-full-recovery` 또는 명시적 `--profile-id full-recovery`로만 사용하고, 노출되는 스케줄은 명시값이 필요하다.

## Verification Evidence

- Focused tests passed:
  - `tests.test_operating_data_orchestrator`
  - `tests.test_data_operations_cli`
  - `tests.test_data_operations_cadence`
- 추가로:
  - `tests.test_operating_data_profile_scheduler`
  - `tests.test_data_operations_cli.DataOperationsCliTests.test_operating_data_profile_scheduler_invocation_plan_command_writes_output_and_markdown`
- 추가 경계 검증:
  - `tests.test_operating_data_profile_scheduler.test_systemd_target_rejects_unsupported_schedule_pattern` (systemd timer로 변환 불가 cron 패턴 선가드)

## Remaining Risks

- 실제 EC2 recurring scheduler deployment는 다음 작업이다.
- 이 작업은 실행 단위 분리이며, 유료 provider나 실거래 broker flow를 추가하지 않는다.
