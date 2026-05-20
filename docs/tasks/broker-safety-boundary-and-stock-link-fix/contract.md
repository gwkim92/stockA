# Task Contract

## Task

- 이름: broker-safety-boundary-and-stock-link-fix
- 요청: broker boundary, 계좌 권한, 주문 한도, kill switch, audit log, paper validation 부재를 해소하고, 종목 목록에서 전체 행이 클릭되는 문제를 고친다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 미래 paper/live 주문은 broker boundary, account permission, order limit, kill switch, paper validation, human approval gate를 통과해야만 승인될 수 있다.
  - 안전 판정은 deterministic Python 코드로 테스트된다.
  - audit-ready DB schema가 존재한다.
  - 실제 broker API 호출, 계좌 로그인, 주문 제출은 구현하지 않는다.
  - `/stocks` 목록에서 행 전체가 아니라 종목 이름/심볼 링크만 클릭된다.

## Why

- 현재 시스템은 추천/보유 충돌을 보여줄 수 있지만, 주문을 안전하게 막는 계층이 없다.
- 실거래를 연결하기 전에 “무엇이 준비되어야 주문을 허용하는지”를 코드와 DB schema로 고정해야 한다.
- 종목 목록은 사용자가 개별 종목을 클릭할 수 있어야 하지만, 행 전체가 링크이면 조작 의도가 모호해진다.

## Scope

- `trading` schema migration 추가.
- 순수 Python 안전 판정 엔진 추가.
- 안전 판정과 migration contract 테스트 추가.
- 종목 목록 row-level link 제거 및 symbol/name 링크만 유지.
- task plan/contract/handoff 갱신.

## Boundaries

- 실거래 broker adapter는 만들지 않는다.
- broker API key, account credential, OAuth, secret file은 만들거나 출력하지 않는다.
- order submission, execution report ingestion, fill 처리, P&L 반영은 하지 않는다.
- FastAPI write endpoint는 만들지 않는다.
- 추천 scoring formula, benchmark, evaluation split은 바꾸지 않는다.
- host scheduler activation은 실행하지 않는다.

## Mutable Surface

- 수정 가능한 파일:
  - `db/migrations/0013_trading_safety_boundary.sql`
  - `src/stockanalysis/trading/*`
  - `tests/test_trading_safety.py`
  - `apps/web/src/app/stocks/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/plans/2026-05-19-broker-safety-boundary-and-stock-link-fix.md`
  - `docs/tasks/broker-safety-boundary-and-stock-link-fix/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_trading_safety`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest discover -s tests`
  - `bash scripts/verify_migrations.sh`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - Playwright snapshot for `http://127.0.0.1:3001/stocks`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task broker-safety-boundary-and-stock-link-fix`
  - `git diff --check`

- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_trading_safety`
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest discover -s tests`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- Playwright snapshot for `http://127.0.0.1:3001/stocks`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task broker-safety-boundary-and-stock-link-fix`
- `git diff --check`

## Verification

- command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_trading_safety`
- command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest discover -s tests`
- command: `bash scripts/verify_migrations.sh`
- command: `cd apps/web && npm run typecheck`
- command: `cd apps/web && npm run build`
- command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task broker-safety-boundary-and-stock-link-fix`
- command: `git diff --check`

## Done Criteria

- [x] safety evaluator blocks by default.
- [x] safety evaluator approves paper/live only when all configured gates pass.
- [x] migration contains broker boundary, account permission, order limits, kill switch, paper validation, and order audit tables.
- [x] `/stocks` row-level link is removed and stock symbol/name link remains clickable.
- [x] required verification passes.
