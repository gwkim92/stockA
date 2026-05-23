# Review

## Result

- completed: `/data-health` 무료 API 예산 `0/0` 표시 원인을 고치고 EC2에 배포했다.
- deployed app commit: `7a2614e`
- root cause: `provider_budget` reader가 `as_of_date=2026-05-23`만 조회했고, ledger에는 최신 row가 `2026-05-22`까지라 `day_missing` empty budget을 반환했다.
- fix: `/api/data-health`에서만 opt-in latest-day fallback을 사용하고, fallback 결과는 `status=stale`로 표시한다.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_market_price_free_backfill tests.test_frontend_live_adapter`
  - result: passed, 67 tests
- verification command: `cd apps/web && npm run typecheck`
  - result: passed
- verification command: `cd apps/web && npm run build`
  - result: passed
- verification command: `git diff --check`
  - result: passed
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task provider-budget-latest-ledger-fallback`
  - result: passed
- verification command: EC2 deploy and service smoke
  - result: passed; app reset to `7a2614e`, Python tests passed, Next build passed, API/web services active
- verification command: EC2 `/api/data-health` provider budget smoke
  - result: passed; `status=stale`, `budget_date=2026-05-22`, `remaining_request_count=8`, `daily_budget=24`
- verification command: EC2 `/data-health?refresh=7a2614e` browser/HTML smoke
  - result: passed; visible text shows `8/24회 남음` and no `0/0`

## Notes

- This does not modify scheduler cadence or Twelve Data usage policy.
- If budget should reset on weekends even without a run, that is a separate product decision. Current behavior intentionally shows latest known ledger with `stale` status.
