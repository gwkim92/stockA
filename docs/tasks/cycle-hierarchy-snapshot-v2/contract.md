# Task Contract

## Task

- 이름: cycle-hierarchy-snapshot-v2
- 요청: 거시/도메인/테마 node 단위 cycle 상태와 전이 로그를 저장한다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 기존 테마 cycle snapshot과 신규 hierarchical propagation evidence를 조합해 node별 `cycle_level`, `cycle_state`, `cycle_score`, `event_heat_score`, `parent_alignment_score`, `conflict_flags`를 저장하고, 급격한 상태 변화를 hysteresis로 완화한다.

## Scope

- 포함:
  - v2 cycle hierarchy snapshot table
  - v2 transition log table
  - node input lookup SQL
  - deterministic scoring/hysteresis
  - `cycle-hierarchy-snapshot-v2-run` CLI
  - unit/bootstrap/AWH 검증
- 제외:
  - recommendation score formula 변경
  - frontend `/cycle-map` 구현
  - GraphRAG community summary
  - 실거래 또는 broker submit

## Mutable Surface

- 수정 가능한 파일:
  - `db/migrations/`
  - `src/stockanalysis/signal/`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `tests/`
  - `docs/tasks/cycle-hierarchy-snapshot-v2/`
- 수정 금지 파일:
  - `.env`와 secret 값
  - broker/live order submission
  - benchmark/evaluation split

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cycle_hierarchy_snapshot_v2 tests.test_data_operations_cli tests.test_operating_data_orchestrator`
  - `bash scripts/verify_seed_bootstrap.sh`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m awh verify --repo . --task cycle-hierarchy-snapshot-v2`

## Done Criteria

- `signal.cycle_hierarchy_state_snapshot`와 `signal.cycle_hierarchy_transition_log`가 migration으로 생성된다.
- node별 score component와 conflict flags가 저장된다.
- 이전 상태와 새 점수 차이가 작으면 hysteresis로 급격한 전이를 막는다.
- 기존 `cycle-state-snapshot`은 깨지지 않는다.
