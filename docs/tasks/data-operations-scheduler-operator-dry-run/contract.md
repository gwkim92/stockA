# Task Contract

## Task

- 이름: data-operations-scheduler-operator-dry-run
- 요청: actual `launchctl bootstrap` 전에 activation runbook을 repo-outside temporary paths로 리허설한다.
- 담당: Codex
- 날짜: 2026-05-11

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: operator가 실제 host scheduler state를 바꾸지 않고 runtime env readiness, scheduler preflight, install dry-run rendering, alert rule validation, evidence bundle 생성을 한 번에 리허설할 수 있다.

## Why

- activation runbook은 문서다. 실제 활성화 전에 문서 절차가 기존 스크립트와 맞는지 자동 리허설해야 한다.
- `launchctl bootstrap`은 host 상태를 바꾸므로 별도 명시 승인 전까지 dry-run evidence만 만든다.

## Scope

- 포함:
  - operator dry-run report builder
  - repo-outside output dir 기반 dry-run wrapper script
  - unit tests and verification script
  - docs/task handoff/roadmap updates
- 제외:
  - 실제 `launchctl` 실행
  - `~/Library/LaunchAgents` 쓰기
  - production env file 생성
  - live provider network credential validation
  - Alertmanager receiver routing
  - DB schema changes
  - write APIs, RBAC, broker/order flow
  - benchmark/scoring/evaluation split 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/scheduler_operator_dry_run.py`
  - `tests/test_data_operations_scheduler_operator_dry_run.py`
  - `scripts/dry_run_data_operations_scheduler_operator_flow.sh`
  - `scripts/verify_data_operations_scheduler_operator_dry_run.sh`
  - `docs/data-operations-scheduler-operator-dry-run.md`
  - `docs/data-operations-scheduler-activation-runbook.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - prior data-operations verification scripts that assert immediate next task
  - `docs/plans/2026-05-11-data-operations-scheduler-operator-dry-run.md`
  - `docs/tasks/data-operations-scheduler-operator-dry-run/`
- 수정 금지 파일:
  - `db/migrations/`
  - production env/secrets/deployment files
  - host scheduler paths
  - benchmark/evaluation/scoring files
  - broker/order implementation
  - unrelated `ai-retrieval-graph-foundation` local documents

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_data_operations_scheduler_operator_dry_run.sh`
  - `bash scripts/verify_data_operations_scheduler_activation_runbook.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `/tmp/stockanalysis-fastapi-venv/bin/python -m unittest discover -s tests`
  - `git diff --check`

## Deliverables

- Operator dry-run wrapper script
- Secret-free operator dry-run report builder
- Verification script
- Docs and handoff updates

## Completion Criteria

- [x] dry-run uses only repo-outside env/output/artifact paths.
- [x] dry-run performs readiness, scheduler preflight, install dry-run render, and alert rule validation.
- [x] dry-run writes an evidence report without secret env values.
- [x] dry-run does not execute child data operation command.
- [x] dry-run does not execute `launchctl` or write host LaunchAgents.
- [x] roadmap moves fixed next task after completion.
- [x] verification commands pass and evidence is recorded.

## Risks

- This does not activate recurring jobs.
- Real env credentials are not validated against provider networks.
- Future host activation still requires explicit user approval.
