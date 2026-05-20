# Task Contract

## Task

- 이름: data-operations-live-scheduler-activation-request
- 요청: activation approval gate를 통과한 evidence를 사용자 승인 요청 패킷으로 변환한다.
- 담당: Codex
- 날짜: 2026-05-11

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 승인된 approval gate와 operator dry-run evidence가 있어도 scheduler activation은 `pending_explicit_user_approval` 상태로 남고, 실제 `launchctl` 실행이나 host LaunchAgents 쓰기는 발생하지 않는다.

## Why

- approval gate의 `activation_allowed=true`는 metadata/evidence가 유효하다는 뜻이지, 사용자가 이 세션에서 실제 host 변경을 승인했다는 뜻이 아니다.
- 다음 세션 또는 다른 에이전트가 gate 통과 상태를 실제 activation 허가로 오해하지 않도록 별도 요청 패킷이 필요하다.

## Scope

- 포함:
  - activation request report builder
  - repo-outside evidence 기반 wrapper script
  - pending/approved boundary unit tests
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
  - `src/stockanalysis/operations/scheduler_activation_request.py`
  - `tests/test_data_operations_scheduler_activation_request.py`
  - `scripts/request_data_operations_live_scheduler_activation.sh`
  - `scripts/verify_data_operations_live_scheduler_activation_request.sh`
  - `docs/data-operations-live-scheduler-activation-request.md`
  - `docs/data-operations-scheduler-activation-approval-gate.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - prior data-operations verification scripts that assert immediate next task
  - `docs/plans/2026-05-11-data-operations-live-scheduler-activation-request.md`
  - `docs/tasks/data-operations-live-scheduler-activation-request/`
- 수정 금지 파일:
  - `db/migrations/`
  - production env/secrets/deployment files
  - host scheduler paths
  - benchmark/evaluation/scoring files
  - broker/order implementation
  - unrelated `ai-retrieval-graph-foundation` local documents

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_data_operations_live_scheduler_activation_request.sh`
  - `bash scripts/verify_data_operations_scheduler_activation_approval_gate.sh`
  - `bash scripts/verify_data_operations_scheduler_operator_dry_run.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=src /tmp/stockanalysis-full-venv/bin/python -m unittest discover -s tests`
  - `git diff --check`

## Deliverables

- Activation request report builder
- Activation request wrapper script
- Verification script
- Docs and handoff updates

## Completion Criteria

- [x] approval gate must be `approved_for_manual_activation`.
- [x] request output stays `pending_explicit_user_approval`.
- [x] request output includes approve/deny decision values.
- [x] final reports do not contain secret env values.
- [x] no script executes `launchctl` or writes host LaunchAgents.
- [x] roadmap moves fixed next task to user decision gate.
- [x] verification commands pass and evidence is recorded.

## Risks

- This does not activate recurring jobs.
- A future task still requires the user to explicitly approve or deny live activation.
- Real provider credential reachability remains separate from this request.
