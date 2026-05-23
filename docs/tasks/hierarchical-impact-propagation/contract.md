# Task Contract

## Task

- 이름: hierarchical-impact-propagation
- 요청: 상위 흐름 뉴스 impact를 classification graph edge를 따라 multi-hop으로 전파하고, 종목 exposure에 연결되는 경로를 저장한다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 거시/도메인/테마 뉴스 impact가 `원천 node -> 하위 node path -> 종목 exposure`로 전파되고, depth/path_weight/decay/confidence가 저장되어 추천·보유 검토와 화면에서 경로 설명에 사용할 수 있다.

## Scope

- 포함:
  - v2 propagation table 추가
  - recursive SQL graph neighborhood lookup
  - path/depth/decay 기반 impact 계산
  - idempotent upsert
  - `hierarchical-impact-propagation-run` CLI
  - unit/bootstrap/AWH 검증
- 제외:
  - recommendation formula 변경
  - cycle hierarchy snapshot v2
  - frontend `/cycle-map` 구현
  - 실거래 또는 broker submit

## Mutable Surface

- 수정 가능한 파일:
  - `db/migrations/`
  - `src/stockanalysis/signal/`
  - `src/stockanalysis/operations/cli.py`
  - `tests/`
  - `scripts/verify_migrations.sh`
  - `docs/tasks/hierarchical-impact-propagation/`
- 수정 금지 파일:
  - `.env`와 secret 값
  - broker/live order submission
  - benchmark/evaluation split

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_hierarchical_impact_propagation tests.test_data_operations_cli`
  - `bash scripts/verify_seed_bootstrap.sh`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m awh verify --repo . --task hierarchical-impact-propagation`

## Done Criteria

- `signal.hierarchical_propagated_instrument_impact`가 migration으로 생성된다.
- Fed/rates 뉴스가 `MACRO_RATES_FED -> TECH_DOMAIN -> AI_SEMICONDUCTOR_CYCLE -> NVDA/MSFT` 같은 multi-hop 후보를 만들 수 있다.
- 같은 event/source node/propagated node/instrument/path 조합 재실행이 중복 row를 만들지 않는다.
- 기존 `macro-event-propagation-run`은 깨지지 않는다.
