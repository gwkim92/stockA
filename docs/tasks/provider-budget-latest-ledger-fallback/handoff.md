# Session Handoff

## Current Status

- 상태: completed
- completed: provider budget ledger가 오늘 row missing일 때 `/api/data-health`에서 최신 이전 ledger day로 fallback하고, `/data-health`가 `0/0` 대신 최신 예산을 보여주도록 수정/배포했다.
- 기준일: 2026-05-23

## Investigation

- EC2 ledger path `/opt/stockanalysis/runtime/market-price-budget-ledger.json` exists.
- ledger provider is `twelve_data`.
- ledger days are `2026-05-20`, `2026-05-21`, `2026-05-22`.
- `/data-health` 기준일은 `2026-05-23`이라 오늘 row가 없고, 기존 reader는 이 경우 `day_missing` empty budget을 반환해 화면이 `0/0`으로 보인다.
- root cause: data health는 현재 날짜를 기준으로 provider budget을 조회하지만, 주말/비거래일 또는 아직 market daily가 돌지 않은 날에는 최신 ledger day를 fallback하지 않는다.

## Completed

- `load_market_price_provider_budget_status(..., fallback_to_latest_day=True)` 옵션을 추가했다.
- 기본 호출에서는 기존 `day_missing` 동작을 유지한다.
- `/api/data-health`의 provider budget 조회에서만 latest-day fallback을 켰다.
- fallback이 사용되면 `status=stale`, `budget_date=<latest ledger day>`를 반환해 당일 기록이 아니라는 사실을 유지한다.
- EC2에서 실제 응답이 `as_of_date=2026-05-23`, `budget_date=2026-05-22`, `remaining_request_count=8`, `daily_budget=24`, `status=stale`로 바뀐 것을 확인했다.
- `/data-health` 화면에서 호출 예산이 `0/0`이 아니라 `8/24`와 `8/24회 남음`으로 보이는 것을 확인했다.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_market_price_free_backfill tests.test_frontend_live_adapter`: passed, 67 tests.
- `cd apps/web && npm run typecheck`: passed.
- `cd apps/web && npm run build`: passed.
- `git diff --check`: passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task provider-budget-latest-ledger-fallback`: passed.
- EC2 deploy at `7a2614e`: Python tests passed, Next build passed, `stockanalysis-frontend-api.service` and `stockanalysis-web.service` active.
- EC2 API smoke: provider budget returned `{"status":"stale","provider":"twelve_data","budget_date":"2026-05-22","daily_budget":24,"used_request_count":16,"remaining_request_count":8,"as_of_date":"2026-05-23"}`.
- EC2 web smoke: `/data-health?refresh=7a2614e` visible text contains `8/24회 남음` and does not contain `0/0`.
- Playwright snapshot: `http://127.0.0.1:13000/data-health?refresh=7a2614e` shows 호출 예산 `8/24`.

## Remaining

- 이 작업은 표시 오류를 고친 것이다. 실제 Twelve Data 호출량 정책이 `daily_budget=24`로 설정된 이유와 하루 허용치 설계는 별도 작업에서 점검 가능하다.
- 전체 사이트 IA 정리는 별도 큰 작업으로 남아 있다.

## Mutable Surface

- `src/stockanalysis/operations/market_price_free_backfill.py`
- `src/stockanalysis/frontend/live_adapter.py`
- `tests/test_market_price_free_backfill.py`
- `tests/test_frontend_live_adapter.py`
- `docs/tasks/provider-budget-latest-ledger-fallback/*`

## Exact Next Step

- exact next step: 다음 작업은 전체 사이트 IA 재정리 또는 데이터 수집/분석 상세 화면 구조 개선 중 하나를 새 task contract로 시작한다.
