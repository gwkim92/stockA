# Task Contract

## Task

- 이름: data-operations-scheduler-install-dry-run
- 요청: generic data operations scheduler wrapper를 호출하는 host scheduler artifact를 실제 설치 없이 dry-run으로 렌더링하고 검증한다.
- 담당: Codex
- 날짜: 2026-05-06

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: repo 밖 output dir에 launchd plist와 manifest JSON을 렌더링할 수 있고, 렌더링된 artifact가 `scripts/run_data_operations_scheduler_job.sh`를 repo 밖 env file로 호출하며 host scheduler 경로에는 아무것도 설치하지 않는다.

## Why

- scheduler activation boundary는 wrapper contract를 고정했다. 다음 단계는 host scheduler artifact가 그 wrapper를 올바르게 호출하는지 실제 설치 없이 확인하는 것이다.
- host scheduler path와 secret/env file이 섞이면 운영 사고가 되므로 dry-run renderer부터 검증해야 한다.

## Scope

- 포함:
  - launchd dry-run renderer Python helper
  - `scripts/render_data_operations_scheduler_install.sh`
  - repo-outside output/env validation
  - daily/weekly cadence schedule rendering
  - monthly first-business-day explicit rejection
  - dry-run manifest JSON
  - no host install artifact guard
  - docs/task handoff/roadmap 갱신
- 제외:
  - actual scheduler install/activation
  - `launchctl bootstrap`
  - cron/GitHub Actions renderer
  - production env file or real credentials
  - provider network credential validation
  - DB schema changes
  - write APIs, RBAC, broker/order flow
  - benchmark/scoring/evaluation split 변경
  - unrelated `ai-retrieval-graph-foundation` local documents

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/scheduler_install.py`
  - `tests/test_data_operations_scheduler_install.py`
  - `scripts/render_data_operations_scheduler_install.sh`
  - `scripts/verify_data_operations_scheduler_install_dry_run.sh`
  - `docs/data-operations-scheduler-install-dry-run.md`
  - `docs/data-operations-scheduler-activation-boundary.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `scripts/verify_data_operations_scheduler_activation_boundary.sh`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/plans/2026-05-06-data-operations-scheduler-install-dry-run.md`
  - `docs/tasks/data-operations-scheduler-install-dry-run/`
- 수정 금지 파일:
  - `db/migrations/`
  - production env/secrets/deployment files
  - benchmark/evaluation/scoring files
  - broker/order implementation
  - unrelated `ai-retrieval-graph-foundation` local documents

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_data_operations_scheduler_install_dry_run.sh`
  - `bash scripts/verify_data_operations_scheduler_activation_boundary.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=src python3 -m unittest discover -s tests`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task data-operations-scheduler-install-dry-run`
  - `git diff --check`

## Deliverables

- Launchd dry-run renderer helper
- Repo-outside render script
- Verification script
- Docs and handoff updates

## Completion Criteria

- [x] renderer refuses repo-inside output dirs.
- [x] renderer refuses repo-inside env files.
- [x] rendered plist calls `scripts/run_data_operations_scheduler_job.sh`.
- [x] rendered plist includes env file, job id, timeout, command, and schedule.
- [x] dry-run manifest is secret-free and points to rendered plist/logs.
- [x] monthly first-business-day jobs are explicitly rejected until a safe calendar strategy exists.
- [x] no host scheduler path is written.
- [x] roadmap moves fixed next task after completion.
- [x] verification commands pass and evidence is recorded.

## Risks

- This does not install or enable launchd.
- This does not validate provider credentials against remote APIs.
- Only launchd dry-run is implemented; cron/GitHub Actions remain future tasks.
