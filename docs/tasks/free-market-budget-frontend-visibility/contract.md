# Task Contract

## Task

- 이름: free-market-budget-frontend-visibility
- 요청: 무료 Alpha Vantage provider budget ledger 상태를 FastAPI data-health DTO와 Next.js data-health 화면에 노출한다.
- 담당: Codex
- 날짜: 2026-05-17

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/api/data-health`가 provider budget ledger의 안전한 요약을 반환하고, `/data-health` 화면이 오늘 남은 무료 market data 호출 수와 최근 runner 상태를 보여준다.

## Why

- watchlist/ledger runner가 생겼지만 현재는 CLI/file 기반이라 운영자가 화면에서 무료 호출 예산을 확인할 수 없다.
- broad market backfill 전에 남은 quota가 UI에 보여야 실수로 provider quota를 소진하지 않는다.

## Scope

- 포함:
  - `STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH` 기반 read-only ledger status reader
  - `/api/data-health` DTO의 `provider_budget` 필드
  - Next.js `/data-health` budget 카드
  - unit/type/build 검증
  - local runtime env 반영
- 제외:
  - DB schema 변경
  - write endpoint
  - scheduler actual activation
  - positive-budget provider 호출
  - paid provider 도입

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/market_price_free_backfill.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_market_price_free_backfill.py`
  - `tests/test_frontend_live_adapter.py`
  - task docs
- 수정 금지 파일:
  - `db/migrations/`
  - API keys and token values
  - broker/order flow
  - host scheduler activation files

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_market_price_free_backfill tests.test_frontend_live_adapter -v`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - authorized `GET http://127.0.0.1:8787/api/data-health`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task free-market-budget-frontend-visibility`

## Completion Criteria

- [x] API does not expose ledger file path or secrets.
- [x] API returns not-configured status when env path is missing.
- [x] API returns configured daily budget, used, remaining, and latest run summary when ledger exists.
- [x] Frontend renders budget status without client-side token exposure.
- [x] Tests and Next build pass.

## Risks

- Ledger is local host state, not a provider-side source of truth.
- Existing running FastAPI process may require restart to load new code/env.
