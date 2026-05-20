# Task Contract

## Task

- 이름: paper-trading-quality-gate
- 요청: 추천 품질, 가상 거래(Paper), 실거래 전 안전 경계, 사람이 이해할 수 있는 거래 준비 화면을 진행한다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/paper-trading`에서 현재 추천과 가상 포트폴리오(Paper) 보유 상태의 충돌을 확인할 수 있다.
  - `/api/paper-trading/preview`는 live DB에서 read-only 가상 거래 후보를 반환한다.
  - 실제 주문, 증권사 API, 계좌 연결, write endpoint는 구현하지 않는다.
  - 추천 품질은 measured outcomes, average alpha, hit rate, 미측정 추천 수로 표시한다.

## Why

- 실거래를 켜기 전에 시스템이 현재 추천과 보유 상태를 일관되게 해석하는지 확인해야 한다.
- 현재 live DB에는 `AAPL` 추천이 `exclude`인데 paper 포트폴리오가 보유 중인 충돌이 보인다. 이런 충돌은 주문보다 먼저 품질 gate로 드러나야 한다.
- 가상 거래 ledger write를 만들기 전에도, 어떤 가상 조치가 필요한지 read-only preview로 검증할 수 있다.

## Scope

- FastAPI live adapter에 가상 거래 preview read DTO를 추가한다.
- Fixture contract와 Next.js 페이지를 추가한다.
- 화면은 한국어 운용 문맥으로 작성한다.
- 하네스 문서에 실거래와 scheduler 활성화 경계를 다시 남긴다.

## Boundaries

- 증권사/order flow, real trading, write API, RBAC, audit write model은 구현하지 않는다.
- DB schema는 바꾸지 않는다.
- 추천 scoring formula, benchmark, evaluation split은 바꾸지 않는다.
- host scheduler activation은 실행하지 않는다.
- `.env`, API key, DB URL, bearer token은 출력하지 않는다.

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `src/stockanalysis/frontend/pagination.py`
  - `apps/web/src/app/layout.tsx`
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/app/paper-trading/page.tsx`
  - `apps/web/src/lib/frontend-api.ts`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/korean-labels.ts`
  - `docs/api/frontend/contract-index.json`
  - `docs/api/frontend/examples/paper-trading-preview.json`
  - `docs/frontend-api-contract.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `tests/test_frontend_api_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `tests/test_frontend_fixture_server.py`
  - `docs/plans/2026-05-19-paper-trading-quality-gate.md`
  - `docs/tasks/paper-trading-quality-gate/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_api_adapter tests.test_frontend_live_adapter tests.test_frontend_fixture_server`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest discover -s tests`
  - `python3 -m json.tool docs/api/frontend/contract-index.json`
  - `python3 -m json.tool docs/api/frontend/examples/paper-trading-preview.json`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - live HTTP smoke for `/api/paper-trading/preview` and `/paper-trading`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task paper-trading-quality-gate`
  - `git diff --check`

## Done Criteria

- [x] `/api/paper-trading/preview`가 fixture와 live에서 동작한다.
- [x] `/paper-trading` 화면이 가상 거래 후보와 추천 품질 요약을 보여준다.
- [x] 실거래와 write API가 추가되지 않았음이 문서와 검증에 남는다.
- [x] 필요한 검증이 통과한다.
