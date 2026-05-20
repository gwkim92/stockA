# Task Contract

## Task

- 이름: data-operations-scheduler-activation-runbook
- 요청: actual scheduler install 전에 수동 승인, rollback, disable, evidence checklist를 고정한다.
- 담당: Codex
- 날짜: 2026-05-06

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: Data Operations scheduler를 실제 host scheduler에 설치하기 전에 따라야 할 수동 activation runbook, rollback/disable 절차, evidence checklist, 검증 스크립트가 존재한다.

## Why

- launchd activation은 host scheduler state를 바꾸는 운영 행위다.
- install dry-run과 alert boundary가 있어도 activation 절차, 중단 조건, rollback 증거가 없으면 실제 반복 실행을 켤 수 없다.

## Scope

- 포함:
  - manual activation gate
  - preflight and dry-run sequence
  - launchd activation command reference
  - rollback and disable procedure
  - post-activation evidence checklist
  - verification script and roadmap/handoff updates
- 제외:
  - 실제 `launchctl bootstrap` 실행
  - `~/Library/LaunchAgents` 쓰기
  - production env file 생성
  - Alertmanager receiver routing
  - provider credential/network validation
  - DB schema changes
  - write APIs, RBAC, broker/order flow
  - benchmark/scoring/evaluation split 변경

## Mutable Surface

- 수정 가능한 파일:
  - `docs/data-operations-scheduler-activation-runbook.md`
  - `scripts/verify_data_operations_scheduler_activation_runbook.sh`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `scripts/verify_data_operations_artifact_runner.sh`
  - `scripts/verify_data_operations_cadence_foundation.sh`
  - `scripts/verify_data_operations_runtime_env_readiness.sh`
  - `scripts/verify_data_operations_runtime_smoke.sh`
  - `scripts/verify_data_operations_scheduler_activation_boundary.sh`
  - `scripts/verify_data_operations_scheduler_install_dry_run.sh`
  - `scripts/verify_data_operations_scheduler_alert_boundary.sh`
  - `docs/plans/2026-05-06-data-operations-scheduler-activation-runbook.md`
  - `docs/tasks/data-operations-scheduler-activation-runbook/`
- 수정 금지 파일:
  - `db/migrations/`
  - production env/secrets/deployment files
  - actual host scheduler paths
  - benchmark/evaluation/scoring files
  - broker/order implementation
  - unrelated `ai-retrieval-graph-foundation` local documents

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_data_operations_scheduler_activation_runbook.sh`
  - `bash scripts/verify_data_operations_scheduler_alert_boundary.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `/tmp/stockanalysis-fastapi-venv/bin/python -m unittest discover -s tests`
  - `git diff --check`

## Deliverables

- Data operations scheduler manual activation runbook
- Verification script
- Docs and handoff updates

## Completion Criteria

- [x] runbook states manual approval is required before host activation.
- [x] runbook includes preflight and install dry-run sequence.
- [x] runbook includes launchd activation commands as reference only.
- [x] runbook includes rollback and disable commands.
- [x] runbook includes post-activation evidence checklist.
- [x] verification script proves no host scheduler mutation occurs.
- [x] roadmap moves fixed next task after completion.
- [x] verification commands pass and evidence is recorded.

## Risks

- This does not activate a scheduler.
- Actual activation still requires explicit operator approval and real repo-outside runtime env.
- launchd command details may need macOS operator validation during the future activation dry-run.
