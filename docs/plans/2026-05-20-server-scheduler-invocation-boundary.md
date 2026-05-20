# Server Scheduler Invocation Boundary Plan

생성일: 2026-05-20

## Summary

- `local-ingest-worker-run`을 서버/외부 scheduler가 호출할 수 있도록 secret-free invocation packet을 만든다.
- 이 작업은 scheduler 배포가 아니다. cron/systemd/Kubernetes/managed scheduler 후보별 command/manifest preview만 만든다.
- Mac LaunchAgents, `launchctl`, host install path write/delete는 계속 금지한다.

## Key Changes

- `stockanalysis.operations.server_scheduler_invocation` 모듈을 추가한다.
- `stockanalysis-operations server-scheduler-invocation-plan` CLI를 추가한다.
- report에는 scheduler target, schedule, worker command preview, manifest preview, repo-outside env/report paths, mutation flags를 담는다.
- command preview는 `stockanalysis.operations.cli local-ingest-worker-run`만 가리키며 env 값은 읽거나 출력하지 않는다.

## Test Plan

- Unit tests: target validation, repo-outside env/output path enforcement, secret-free payload, `--worker-execute` opt-in.
- CLI tests: output/markdown write, repo-inside path rejection.
- Verify script: compile, focused unit tests, CLI smoke, no `launchctl`, no `postgresql://`, no secret-like token in generated report.
- Regression: `verify_project_execution_roadmap.sh`, `git diff --check`.

## Assumptions

- local worker는 이미 `/api/data-health`에서 보인다.
- 서버 scheduler 선택/배포는 다음 별도 작업이다.
- 이 작업에서는 실제 scheduler 등록, host mutation, cloud deployment를 하지 않는다.
