# Task Contract

## Task

- 이름: scheduler-activation-market-price-evidence
- 요청: scheduler activation dry-run/evidence path를 `market-price-daily-run --skip-if-fresh` 기준으로 갱신한다.
- 담당: Codex
- 날짜: 2026-05-18

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: host scheduler를 실제 활성화하지 않고, `market-price-daily` operator dry-run evidence와 pending approval gate가 repo-outside 경로에 생성되어 있으며 대표 verification scripts가 현재 `local-live-mvp-runtime` task와 새 market price command를 기준으로 통과한다.

## Scope

- operator dry-run 문서 예시를 `market-price-daily`로 갱신한다.
- runtime env readiness, activation runbook, operator dry-run, approval gate verification scripts의 stale current-task assertion을 현재 roadmap과 맞춘다.
- operator dry-run/approval gate script fixture env에 Twelve Data market price provider/watchlist/ledger를 포함한다.
- repo-outside evidence를 생성하되 `launchctl`, LaunchAgents 쓰기, child data operation 실행은 하지 않는다.

## Mutable Surface

- 수정 가능한 파일:
  - `docs/data-operations-scheduler-operator-dry-run.md`
  - scheduler activation/runtime env verification scripts
  - `docs/tasks/scheduler-activation-market-price-evidence/`
  - `docs/tasks/local-live-mvp-runtime/handoff.md`
  - `docs/tasks/local-live-mvp-runtime/review.md`
- 수정 금지 파일:
  - repo-inside env/secrets
  - host LaunchAgents path
  - DB migrations
  - scoring/benchmark/evaluation split
  - broker/order flow

## Boundaries

- 실제 `launchctl bootstrap`, `kickstart`, `bootout`, `print`는 실행하지 않는다.
- host LaunchAgents 경로에 파일을 쓰지 않는다.
- provider key, DB URL, env 값은 출력하거나 repo에 저장하지 않는다.
- scoring, schema, benchmark, paper trading, real trading은 건드리지 않는다.

## Verification Commands

- 검증에 사용할 명령:
- `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_data_operations_runtime_env_readiness.sh`
- `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_data_operations_scheduler_activation_runbook.sh`
- `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_data_operations_scheduler_operator_dry_run.sh`
- `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_data_operations_scheduler_activation_approval_gate.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task scheduler-activation-market-price-evidence`
- `git diff --check`

## Done Criteria

- [x] `market-price-daily` operator dry-run evidence exists outside the repo.
- [x] pending approval gate exists outside the repo and blocks activation.
- [x] verification scripts use current `local-live-mvp-runtime` roadmap state.
- [x] representative operator dry-run/approval gate commands use `market-price-daily-run --skip-if-fresh`.
