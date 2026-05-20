# Task Contract

## Task

- 이름: server-scheduler-deployment-target-decision
- 요청: 무료 조건과 현재 로컬 런타임 제약에서 실제 반복 scheduler 배포 대상을 결정한다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 현재 조건에서 외부 scheduler를 배포할 수 있는지, 어떤 대상이 추천되는지, 무엇이 blocker인지 secret-free decision packet으로 확인할 수 있다.

## Why

- 사용자는 Mac에 scheduler를 설치하는 이유를 이해하기 어렵다고 했고, 웹 서버 또는 서버 측 scheduler가 자연스럽지 않냐고 질문했다.
- 현재 프로젝트는 로컬 Postgres + 로컬 FastAPI/Next + 로컬 worker가 동작하지만, 외부 scheduler가 접근 가능한 hosted DB/runtime은 아직 없다.
- 무료 조건을 지켜야 하므로 paid managed scheduler나 유료 runner를 전제로 하면 안 된다.

## Scope

- 포함:
  - scheduler target decision builder
  - `stockanalysis-operations server-scheduler-deployment-target-decision` CLI
  - zero-budget/public-repo/local-only DB constraints
  - GitHub Actions/systemd/Kubernetes/managed scheduler candidate matrix
  - tests, verify script, docs/handoff/review
- 제외:
  - 실제 GitHub Actions workflow 생성
  - cron/systemd/Kubernetes/managed scheduler 배포
  - Mac LaunchAgents/`launchctl` actual mutation
  - hosted DB 계정 생성 또는 DB migration
  - secret 등록
  - broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/server_scheduler_deployment_decision.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_server_scheduler_deployment_decision.py`
  - `tests/test_data_operations_cli.py`
  - `scripts/verify_server_scheduler_deployment_target_decision.sh`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `AGENTS.md`
  - task docs
- 수정 금지 파일:
  - `.env` secret values
  - `.github/workflows/*` actual scheduler workflow
  - host scheduler install files
  - DB migrations
  - scoring/evaluation benchmark

## Boundaries

- decision packet은 secret 값을 읽거나 출력하지 않는다.
- 이 작업은 scheduler target decision만 수행하며 배포는 하지 않는다.
- 외부 scheduler가 로컬 `127.0.0.1` Postgres에 닿는 것처럼 가정하지 않는다.
- 무료 조건을 깨는 target은 추천하지 않는다.

## Verification Commands

- 검증에 사용할 명령:
- `PYTHONPATH=src python3 -m unittest tests.test_server_scheduler_deployment_decision tests.test_data_operations_cli.DataOperationsCliTests.test_server_scheduler_deployment_target_decision_command_writes_output_and_markdown tests.test_data_operations_cli.DataOperationsCliTests.test_server_scheduler_deployment_target_decision_rejects_repo_inside_output`
- `bash scripts/verify_server_scheduler_deployment_target_decision.sh`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task server-scheduler-deployment-target-decision`
- `git diff --check`

## Done Criteria

- [x] Current local-only runtime is marked blocked for external scheduler deployment.
- [x] GitHub Actions is recommended only after hosted DB/runtime is configured.
- [x] Existing host/systemd is recommended only when an existing runtime host is available.
- [x] No scheduler deployment file is created.
- [x] Verification evidence is recorded in handoff/review.
