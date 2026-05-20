# Task Contract

## Task

- 이름: trading-readiness-cockpit
- 요청: broker boundary, 계좌 권한, 주문 한도, kill switch, audit log, paper validation 상태를 사용자가 이해할 수 있게 백엔드 read model과 화면에 노출한다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/api/trading/readiness`가 `trading.*` 안전 테이블 상태를 read-only DTO로 반환한다.
  - `/trading-readiness` 화면이 거래 안전 gate의 통과/차단/누락 상태를 한국어로 보여준다.
  - broker secret은 노출하지 않고 configured 여부만 보여준다.
  - order submission, broker adapter, credential handling, fill 처리, 실거래 write API는 구현하지 않는다.

## Why

- 이전 작업에서 안전 schema와 evaluator는 생겼지만, 사용자는 화면에서 현재 무엇이 준비됐고 무엇이 막혀 있는지 볼 수 없다.
- 실거래 또는 paper ledger write로 가기 전에, 안전 gate 상태를 운영 cockpit에서 검증 가능하게 만들어야 한다.

## Scope

- frontend API contract에 trading readiness endpoint 추가.
- live adapter SQL read model 추가.
- Next.js 거래 안전 점검 화면 추가.
- 한국어 wording과 문서/handoff 갱신.
- 테스트와 브라우저 확인 수행.

## Boundaries

- 실거래 broker adapter는 만들지 않는다.
- broker API key, OAuth token, account credential, DB URL, read token은 출력하거나 저장하지 않는다.
- FastAPI write endpoint는 만들지 않는다.
- `trading.order_intent_audit`는 읽기만 한다.
- 추천 scoring, benchmark, evaluation split, scheduler activation은 바꾸지 않는다.

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `docs/api/frontend/contract-index.json`
  - `docs/api/frontend/examples/trading-readiness.json`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/frontend-api.ts`
  - `apps/web/src/lib/korean-labels.ts`
  - `apps/web/src/app/layout.tsx`
  - `apps/web/src/app/paper-trading/page.tsx`
  - `apps/web/src/app/trading-readiness/page.tsx`
  - `apps/web/src/app/globals.css`
  - `tests/test_frontend_live_adapter.py`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `docs/tasks/trading-readiness-cockpit/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter tests.test_frontend_api_adapter tests.test_frontend_fixture_server tests.test_trading_safety`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest discover -s tests`
  - `cd apps/web && npm run typecheck && npm run build`

- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter tests.test_frontend_api_adapter tests.test_trading_safety`
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest discover -s tests`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- Browser snapshot for `http://127.0.0.1:3001/trading-readiness`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task trading-readiness-cockpit`
- `git diff --check`

## Verification

- command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter tests.test_frontend_api_adapter tests.test_frontend_fixture_server tests.test_trading_safety`
- command: `bash scripts/verify_frontend_api_contract.sh`
- command: `bash scripts/verify_frontend_api_adapter.sh`
- command: `bash scripts/verify_frontend_fixture_server.sh`
- command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest discover -s tests`
- command: `cd apps/web && npm run typecheck`
- command: `cd apps/web && npm run build`
- command: live FastAPI `/api/trading/readiness` authorized smoke
- command: Browser check for `http://127.0.0.1:3001/trading-readiness`
- command: `bash scripts/verify_project_execution_roadmap.sh`
- command: `git diff --check`

## Done Criteria

- [x] `/api/trading/readiness` is live-supported and fixture-supported.
- [x] readiness SQL reads canonical `trading.*` safety tables without writes.
- [x] DTO exposes no secret values.
- [x] `/trading-readiness` renders safety gates and next steps in Korean.
- [x] required verification passes.
