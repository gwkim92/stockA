# Session Handoff

## Active Task

- 이름: server-scheduler-invocation-boundary
- 담당: Codex
- 날짜: 2026-05-20

## Current Status

- 완료:
  - task contract and implementation plan created.
  - `stockanalysis.operations.server_scheduler_invocation` report builder and markdown renderer added.
  - `stockanalysis-operations server-scheduler-invocation-plan` CLI added.
  - cron/systemd/Kubernetes/managed scheduler manifest previews added.
  - focused unit/CLI tests added.
  - `scripts/verify_server_scheduler_invocation_boundary.sh` added.
  - roadmap, AGENTS, and verification plan updated.
- 막힌 점:
  - 없음.

## Exact Next Step

- 다음 세션은 이것부터 시작: `server-scheduler-deployment-target-decision`에서 실제 운영 대상이 VPS/systemd, container/Kubernetes, GitHub Actions, managed scheduler 중 무엇인지 선택한다.
- 다음 작업은 `server-scheduler-deployment-target-decision`로 두고, 실제 운영 대상이 VPS/systemd, container/Kubernetes, GitHub Actions, managed scheduler 중 무엇인지 선택한다.
- 금지: 이 handoff만으로 실제 cron/systemd/Kubernetes/managed scheduler 배포, Mac LaunchAgents write/delete, `launchctl bootstrap/kickstart`를 실행하지 않는다.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_server_scheduler_invocation tests.test_data_operations_cli.DataOperationsCliTests.test_server_scheduler_invocation_plan_command_writes_output_and_markdown tests.test_data_operations_cli.DataOperationsCliTests.test_server_scheduler_invocation_plan_rejects_repo_inside_env`
- `bash scripts/verify_server_scheduler_invocation_boundary.sh`
- `bash scripts/verify_project_execution_roadmap.sh`
- `python3 -m compileall src tests`
- `git diff --check`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task server-scheduler-invocation-boundary`

## Risks

- 이 작업은 호출 패킷만 만든다. 반복 실행 자체는 아직 배포되지 않았다.
- 실제 server scheduler 대상별 env injection, container image, log/alert integration은 다음 별도 작업이다.
- `--worker-execute`를 넣은 command preview는 실제 데이터 적재용이므로 운영 배포 전 수동 live smoke evidence가 필요하다.
