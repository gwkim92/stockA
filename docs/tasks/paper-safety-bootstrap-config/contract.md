# Task Contract

## Task

- 이름: paper-safety-bootstrap-config
- 요청: trading readiness에서 누락된 broker boundary, account permission, order limit policy를 실제 브로커 없이 paper 전용 설정으로 등록하는 workflow를 구현한다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - simulated paper broker boundary가 `enabled`, `supports_order_preview=true`, `supports_order_submit=false`로 upsert될 수 있다.
  - paper account permission이 `paper_trade`, `active`, bounded notional limit으로 upsert될 수 있다.
  - paper order limit policy가 `active`로 upsert될 수 있다.
  - global kill switch는 기본 해제하지 않는다.
  - broker secret, broker API, 실제 주문 제출은 구현하지 않는다.

## Boundaries

- 실제 broker credential, OAuth token, account credential을 만들거나 출력하지 않는다.
- `submitted_to_broker=true`를 만들지 않는다.
- FastAPI write endpoint를 만들지 않는다.
- kill switch 해제는 이 task 범위 밖이다.
- 추천 scoring, benchmark, evaluation split은 바꾸지 않는다.

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/trading/paper_safety_bootstrap.py`
  - `src/stockanalysis/trading/__init__.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_trading_paper_safety_bootstrap.py`
  - `tests/test_data_operations_cli.py`
  - `docs/plans/2026-05-19-paper-safety-bootstrap-config.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `docs/tasks/paper-safety-bootstrap-config/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_trading_paper_safety_bootstrap tests.test_data_operations_cli tests.test_trading_paper_validation tests.test_trading_safety`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest discover -s tests`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task paper-safety-bootstrap-config`
  - `git diff --check`

## Done Criteria

- [x] SQL upserts `trading.broker_boundary`, `trading.account_permission`, `trading.order_limit_policy`.
- [x] SQL keeps `supports_order_submit=false` and never sets `submitted_to_broker=true`.
- [x] report exposes no secret values.
- [x] operations CLI command is covered by tests.
- [x] required verification passes.
