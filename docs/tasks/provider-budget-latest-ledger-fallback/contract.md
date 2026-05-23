# Task Contract

## Task

- 이름: provider-budget-latest-ledger-fallback
- request: `/data-health`의 무료 API 예산이 주말/비거래일에 `0/0`으로 보이는 원인을 고치고, 최신 ledger 기록을 사용자에게 보여준다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- goal: provider budget ledger에 오늘 row가 없더라도 이전 최신 예산 기록이 있으면 `/api/data-health`와 `/data-health`가 `0/0` 대신 최신 예산 기록과 기준일을 보여준다.
- 오늘 row가 실제로 없고 ledger 자체도 비어 있으면 기존처럼 `day_missing`/`0` 상태를 유지한다.
- ledger path, API key, DB URL 같은 민감 정보는 응답과 화면에 노출하지 않는다.

## Scope

- 포함:
  - provider budget reader의 최신 ledger fallback
  - frontend live adapter에서 fallback 사용
  - 관련 단위 테스트
  - task handoff/review
- 제외:
  - 실제 market price runner 주기 변경
  - Twelve Data 호출/소진 로직 변경
  - scheduler timer 변경
  - env 파일 또는 secret 수정

## Mutable Surface

- mutable surface: `src/stockanalysis/operations/market_price_free_backfill.py`, `src/stockanalysis/frontend/live_adapter.py`, `tests/test_market_price_free_backfill.py`, `tests/test_frontend_live_adapter.py`, `docs/tasks/provider-budget-latest-ledger-fallback/*`.
- 수정 금지:
  - `.env`
  - EC2 env 파일
  - systemd unit/timer 설정
  - market price provider API key
  - DB schema/migrations

## Acceptance Criteria

- `/api/data-health` provider budget가 오늘 row missing + 과거 ledger 존재 상황에서 `daily_budget > 0`과 최신 `budget_date`를 반환한다.
- 상태는 당일 기록이 아니라는 사실을 알 수 있게 `stale`로 표시한다.
- 기존 day-missing 동작은 fallback을 요청하지 않는 호출에서는 유지된다.
- `/data-health` 화면에서 무료 API 예산이 `0/0`으로 보이지 않는다.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_market_price_free_backfill tests.test_frontend_live_adapter`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task provider-budget-latest-ledger-fallback`
- verification command: EC2 `/api/data-health` and `/data-health` smoke verifying provider budget no longer renders `0/0`.
