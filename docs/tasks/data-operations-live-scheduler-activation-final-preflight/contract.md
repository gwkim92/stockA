# Task Contract

## Task

- 이름: data-operations-live-scheduler-activation-final-preflight
- 요청: user decision 이후 host scheduler activation plan 전 마지막 evidence/runtime preflight를 만든다.
- 담당: Codex
- 날짜: 2026-05-11

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: approve decision, request, approval gate, operator dry-run, fresh runtime readiness가 모두 유효할 때만 host activation plan으로 이동 가능하며, 이 task 안에서는 `launchctl` 실행이나 host LaunchAgents 쓰기가 발생하지 않는다.

## Why

- approve decision 이후에도 실제 host mutation 직전에는 현재 runtime env가 여전히 준비되어 있는지 재검증해야 한다.
- 승인 기록이 오래되었거나 runtime env가 깨진 상태에서 host scheduler activation plan으로 넘어가면 운영 사고가 된다.

## Scope

- 포함:
  - final preflight report builder
  - repo-outside final preflight wrapper script
  - approved/denied/runtime-failed unit tests
  - verification script
  - docs/task handoff/roadmap updates
- 제외:
  - 실제 `launchctl` 실행
  - `~/Library/LaunchAgents` 쓰기
  - production env file 생성
  - provider network calls
  - Alertmanager receiver routing
  - DB schema changes
  - write APIs, RBAC, broker/order flow
  - benchmark/scoring/evaluation split 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/scheduler_activation_final_preflight.py`
  - `tests/test_data_operations_scheduler_activation_final_preflight.py`
  - `scripts/preflight_data_operations_live_scheduler_activation.sh`
  - `scripts/verify_data_operations_live_scheduler_activation_final_preflight.sh`
  - `docs/data-operations-live-scheduler-activation-final-preflight.md`
  - `docs/data-operations-live-scheduler-activation-user-decision.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - prior data-operations verification scripts that assert immediate next task
  - `docs/plans/2026-05-11-data-operations-live-scheduler-activation-final-preflight.md`
  - `docs/tasks/data-operations-live-scheduler-activation-final-preflight/`
- 수정 금지 파일:
  - `db/migrations/`
  - production env/secrets/deployment files
  - host scheduler paths
  - benchmark/evaluation/scoring files
  - broker/order implementation
  - unrelated `ai-retrieval-graph-foundation` local documents

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_data_operations_live_scheduler_activation_final_preflight.sh`
  - `bash scripts/verify_data_operations_live_scheduler_activation_user_decision.sh`
  - `bash scripts/verify_data_operations_live_scheduler_activation_request.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=src /tmp/stockanalysis-full-venv/bin/python -m unittest discover -s tests`
  - `git diff --check`

## Deliverables

- Activation final-preflight report builder
- Activation final-preflight wrapper script
- Verification script
- Docs and handoff updates

## Completion Criteria

- [x] approve decision plus fresh runtime readiness passes final preflight.
- [x] denied decision blocks final preflight.
- [x] failed runtime readiness blocks final preflight.
- [x] final reports do not contain secret env values.
- [x] no script executes `launchctl` or writes host LaunchAgents.
- [x] roadmap moves fixed next task to host activation plan.
- [x] verification commands pass and evidence is recorded.

## Risks

- This does not activate recurring jobs.
- A future host activation plan still must avoid execution until explicit approval for host mutation.
- Runtime readiness is local env validation only, not provider network reachability.
