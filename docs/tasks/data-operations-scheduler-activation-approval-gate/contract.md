# Task Contract

## Task

- 이름: data-operations-scheduler-activation-approval-gate
- 요청: 실제 host scheduler activation 전에 operator dry-run evidence와 명시 승인 record를 검증하는 게이트를 만든다.
- 담당: Codex
- 날짜: 2026-05-11

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: operator dry-run evidence가 없거나 명시 승인 record가 없으면 scheduler activation은 blocked로 판정되고, 승인 record가 있어도 코드가 `launchctl`을 실행하지 않는다.

## Why

- operator dry-run은 evidence를 만들지만, 실제 host scheduler state 변경은 별도 명시 승인이 필요하다.
- 승인 여부를 문서만으로 남기면 다음 세션에서 흔들릴 수 있으므로 machine-readable gate가 필요하다.

## Scope

- 포함:
  - approval gate report builder
  - approval gate wrapper script
  - approved/pending unit tests
  - verification script
  - docs/task handoff/roadmap updates
- 제외:
  - 실제 `launchctl` 실행
  - `~/Library/LaunchAgents` 쓰기
  - production env file 생성
  - live provider credential/network validation
  - Alertmanager receiver routing
  - DB schema changes
  - write APIs, RBAC, broker/order flow
  - benchmark/scoring/evaluation split 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/scheduler_activation_approval.py`
  - `tests/test_data_operations_scheduler_activation_approval.py`
  - `scripts/check_data_operations_scheduler_activation_approval_gate.sh`
  - `scripts/verify_data_operations_scheduler_activation_approval_gate.sh`
  - `docs/data-operations-scheduler-activation-approval-gate.md`
  - `docs/data-operations-scheduler-operator-dry-run.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - prior data-operations verification scripts that assert immediate next task
  - `docs/plans/2026-05-11-data-operations-scheduler-activation-approval-gate.md`
  - `docs/tasks/data-operations-scheduler-activation-approval-gate/`
- 수정 금지 파일:
  - `db/migrations/`
  - production env/secrets/deployment files
  - host scheduler paths
  - benchmark/evaluation/scoring files
  - broker/order implementation
  - unrelated `ai-retrieval-graph-foundation` local documents

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_data_operations_scheduler_activation_approval_gate.sh`
  - `bash scripts/verify_data_operations_scheduler_operator_dry_run.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=src /tmp/stockanalysis-full-venv/bin/python -m unittest discover -s tests`
  - `git diff --check`

## Deliverables

- Approval gate report builder
- Approval gate wrapper script
- Verification script
- Docs and handoff updates

## Completion Criteria

- [x] operator dry-run evidence is required.
- [x] missing approval record returns blocked, not approved.
- [x] approved record requires explicit operator, timestamp, job id, rollback owner, activation window, and risk acknowledgements.
- [x] final reports do not contain secret env values.
- [x] no script executes `launchctl` or writes host LaunchAgents.
- [x] roadmap moves fixed next task after completion.
- [x] verification commands pass and evidence is recorded.

## Risks

- This does not activate recurring jobs.
- A future task still requires a real operator to provide repo-outside evidence and explicit approval.
- Real provider credential reachability remains separate from this gate.
