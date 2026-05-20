# Task Contract

## Task

- 이름: data-operations-live-scheduler-activation-user-decision
- 요청: activation request packet에 대한 사용자의 approve/deny decision record를 검증하는 게이트를 만든다.
- 담당: Codex
- 날짜: 2026-05-11

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: activation request packet이 있어도 decision record가 없으면 activation은 blocked이고, approve decision이 있어도 이 task 안에서는 `launchctl` 실행이나 host LaunchAgents 쓰기가 발생하지 않는다.

## Why

- `pending_explicit_user_approval`은 다음 세션에서 반드시 명시적으로 풀어야 하는 상태다.
- approve/deny를 machine-readable record로 남기지 않으면 실제 activation 허가 여부가 대화 맥락에 의존하게 된다.

## Scope

- 포함:
  - activation user-decision report builder
  - repo-outside decision record wrapper script
  - pending/approve/deny unit tests
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
  - `src/stockanalysis/operations/scheduler_activation_decision.py`
  - `tests/test_data_operations_scheduler_activation_decision.py`
  - `scripts/decide_data_operations_live_scheduler_activation.sh`
  - `scripts/verify_data_operations_live_scheduler_activation_user_decision.sh`
  - `docs/data-operations-live-scheduler-activation-user-decision.md`
  - `docs/data-operations-live-scheduler-activation-request.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - prior data-operations verification scripts that assert immediate next task
  - `docs/plans/2026-05-11-data-operations-live-scheduler-activation-user-decision.md`
  - `docs/tasks/data-operations-live-scheduler-activation-user-decision/`
- 수정 금지 파일:
  - `db/migrations/`
  - production env/secrets/deployment files
  - host scheduler paths
  - benchmark/evaluation/scoring files
  - broker/order implementation
  - unrelated `ai-retrieval-graph-foundation` local documents

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_data_operations_live_scheduler_activation_user_decision.sh`
  - `bash scripts/verify_data_operations_live_scheduler_activation_request.sh`
  - `bash scripts/verify_data_operations_scheduler_activation_approval_gate.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=src /tmp/stockanalysis-full-venv/bin/python -m unittest discover -s tests`
  - `git diff --check`

## Deliverables

- Activation user-decision report builder
- Activation user-decision wrapper script
- Verification script
- Docs and handoff updates

## Completion Criteria

- [x] missing decision record returns blocked.
- [x] approve decision allows only final preflight next step, not execution in this task.
- [x] deny decision blocks activation branch.
- [x] final reports do not contain secret env values.
- [x] no script executes `launchctl` or writes host LaunchAgents.
- [x] roadmap moves fixed next task to final preflight.
- [x] verification commands pass and evidence is recorded.

## Risks

- This does not activate recurring jobs.
- A future final preflight task still must validate current evidence before any host mutation.
- Real provider credential reachability remains separate from this decision gate.
