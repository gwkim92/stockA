# Task Contract

## Task

- 이름: paper-validation-audit-writer
- 요청: `/api/paper-trading/preview` 결과를 기반으로 `trading.paper_validation_run`과 `trading.order_intent_audit`를 생성하는 workflow를 구현한다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - paper preview의 가상 조치 후보가 deterministic safety evaluator를 거쳐 audit row로 기록될 수 있다.
  - `trading.paper_validation_run`이 preview hash, 추천 수, 충돌 수, 승인 후보 수, 검증 심볼, 차단 사유와 함께 기록될 수 있다.
  - 모든 audit row는 `submitted_to_broker=false`다.
  - FastAPI write endpoint, broker adapter, broker credential, 실제 주문 제출은 구현하지 않는다.

## Why

- trading readiness 화면은 무엇이 막혔는지 보여주지만, 아직 paper validation/audit row를 생성하는 workflow가 없다.
- 실거래 전에는 “추천 → 가상 조치 → 안전 판정 → 감사 기록”이 먼저 반복 가능해야 한다.

## Scope

- `stockanalysis.trading.paper_validation` 모듈 추가.
- `stockanalysis-operations paper-validation-audit-run` CLI 추가.
- paper validation/audit SQL renderer와 runner 추가.
- unit tests와 docs/handoff 갱신.

## Boundaries

- broker API를 호출하지 않는다.
- broker secret, account credential, OAuth token, DB URL, read token을 출력하지 않는다.
- FastAPI write endpoint를 만들지 않는다.
- 실제 주문, fill, execution report, P&L 반영은 하지 않는다.
- scheduler activation은 하지 않는다.
- 추천 scoring, benchmark, evaluation split은 바꾸지 않는다.

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/trading/paper_validation.py`
  - `src/stockanalysis/trading/__init__.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_trading_paper_validation.py`
  - `tests/test_data_operations_cli.py`
  - `docs/plans/2026-05-19-paper-validation-audit-writer.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `docs/tasks/paper-validation-audit-writer/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_trading_paper_validation tests.test_data_operations_cli tests.test_trading_safety`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest discover -s tests`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task paper-validation-audit-writer`
  - `git diff --check`

## Done Criteria

- [x] paper validation/audit SQL contains `trading.paper_validation_run` and `trading.order_intent_audit`.
- [x] SQL never sets `submitted_to_broker=true`.
- [x] workflow report exposes no secret values.
- [x] operations CLI command is covered by tests.
- [x] required verification passes.
