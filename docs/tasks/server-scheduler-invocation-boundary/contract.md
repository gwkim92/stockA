# Task Contract

## Task

- 이름: server-scheduler-invocation-boundary
- 요청: local ingest worker를 서버 측 scheduler가 호출할 수 있는 안전한 invocation boundary로 정리한다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: repo-outside env/report 경로를 입력하면 cron/systemd/Kubernetes/managed scheduler 후보별로 `stockanalysis-operations local-ingest-worker-run` command/manifest preview를 secret 없이 생성할 수 있다.

## Why

- 사용자는 Mac LaunchAgents보다 웹/서버 측 scheduler가 자연스럽지 않냐고 지적했다.
- 현재 로컬 worker는 수동/프로세스 루프만 가능하다.
- 다음 단계의 실제 scheduler 선택 전에, 어떤 scheduler든 호출해야 할 backend CLI 경계를 먼저 고정해야 한다.

## Scope

- 포함:
  - secret-free server scheduler invocation report builder
  - `stockanalysis-operations server-scheduler-invocation-plan` CLI
  - cron/systemd/Kubernetes/managed scheduler preview
  - tests, verify script, roadmap/verification/handoff docs
- 제외:
  - 실제 cron/systemd/Kubernetes/managed scheduler 배포
  - Mac LaunchAgents/`launchctl` actual mutation
  - DB schema 변경
  - 추천 점수/AI 품질 변경
  - broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/server_scheduler_invocation.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_server_scheduler_invocation.py`
  - `tests/test_data_operations_cli.py`
  - `scripts/verify_server_scheduler_invocation_boundary.sh`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `AGENTS.md`
  - task docs
- 수정 금지 파일:
  - `.env` secret values
  - scheduler host install files
  - DB migrations
  - scoring/evaluation benchmark
  - real brokerage/order execution code

## Boundaries

- report는 env 파일 경로만 참조하고 env 값을 읽거나 출력하지 않는다.
- repo-inside env/output 경로는 거부한다.
- 실제 scheduler install/deploy/host mutation은 하지 않는다.
- `--worker-execute`가 없으면 command preview도 preview-only worker command로 만든다.

## Verification Commands

- 검증에 사용할 명령:
- `PYTHONPATH=src python3 -m unittest tests.test_server_scheduler_invocation tests.test_data_operations_cli.DataOperationsCliTests.test_server_scheduler_invocation_plan_command_writes_output_and_markdown tests.test_data_operations_cli.DataOperationsCliTests.test_server_scheduler_invocation_plan_rejects_repo_inside_env`
- `bash scripts/verify_server_scheduler_invocation_boundary.sh`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task server-scheduler-invocation-boundary`
- `git diff --check`

## Done Criteria

- [x] CLI output is secret-free and repo-outside only.
- [x] Generated report states scheduler is not deployed and host mutation is not allowed.
- [x] Command preview calls `local-ingest-worker-run`.
- [x] Target previews exist for cron/systemd/Kubernetes/managed scheduler.
- [x] Verification evidence is recorded in handoff/review.
