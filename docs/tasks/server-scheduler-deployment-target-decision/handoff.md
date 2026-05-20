# Session Handoff

## Active Task

- 이름: server-scheduler-deployment-target-decision
- 담당: Codex
- 날짜: 2026-05-20

## Current Status

- 완료:
  - task contract and implementation plan created.
  - `stockanalysis.operations.server_scheduler_deployment_decision` report builder and markdown renderer added.
  - `stockanalysis-operations server-scheduler-deployment-target-decision` CLI added.
  - current zero-budget local-only state now reports `blocked_missing_hosted_database_or_runtime`.
  - hosted DB/runtime state recommends `github_actions_scheduled_workflow`.
  - existing runtime host state recommends `vps_systemd_timer`.
  - focused unit/CLI tests and verification script added.
  - roadmap, AGENTS, and verification plan updated.
- 막힌 점:
  - 외부 scheduler 배포는 hosted DB/runtime 부재로 차단된다.

## Exact Next Step

- 다음 세션은 이것부터 시작: `hosted-database-runtime-decision`에서 무료 또는 이미 보유한 인프라 기준으로 DB/runtime을 외부에서 접근 가능하게 둘지, 아니면 local-only runner를 유지할지 결정한다.
- 금지: 이 handoff만으로 GitHub Actions workflow, cron, systemd timer, Kubernetes CronJob, managed scheduler, Mac LaunchAgents를 생성/배포하지 않는다.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_server_scheduler_deployment_decision tests.test_data_operations_cli.DataOperationsCliTests.test_server_scheduler_deployment_target_decision_command_writes_output_and_markdown tests.test_data_operations_cli.DataOperationsCliTests.test_server_scheduler_deployment_target_decision_rejects_repo_inside_output`
- `bash scripts/verify_server_scheduler_deployment_target_decision.sh`
- `bash scripts/verify_project_execution_roadmap.sh`
- `python3 -m compileall src tests`
- `git diff --check`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task server-scheduler-deployment-target-decision`

## Risks

- GitHub Actions는 public repo에서 무료 후보지만 현재 로컬 Postgres에는 접근할 수 없다.
- hosted DB/runtime을 고르면 DB credential, network exposure, migrations, backup, quota, 비용/무료 tier 정책을 별도 검토해야 한다.
- local-only runner를 유지하면 Mac이 꺼져 있을 때 자동 수집은 멈춘다.
