# performance-observability-baseline-v1

## Measurement Context

- Date: 2026-07-01
- Local web: `http://127.0.0.1:13003`
- API source: SSH tunnel to EC2 FastAPI `http://127.0.0.1:8787`
- EC2 target: `3.211.40.142`
- Scope: baseline only. No performance tuning was performed.

## Build Baseline

- Command: `cd apps/web && npm run build`
- Result: passed.
- Next.js compile time: `1200ms`
- TypeScript phase: `3.7s`

## Route Timing Baseline

| Route | Status | time_total |
| --- | ---: | ---: |
| `/` | 200 | 2.546896s |
| `/market-map` | 200 | 0.515278s |
| `/cycle-map` | 200 | 0.510357s |
| `/stocks/AAPL` | 200 | 1.066721s |
| `/recommendations/AAPL-professional-2026-06-25` | 200 | 0.484777s |
| `/data-health` | 200 | 1.641536s |

## EC2 Service Baseline

- `stockanalysis-web.service`: active.
- `stockanalysis-web-public-13000.service`: active.
- `stockanalysis-frontend-api.service`: active.
- `http://127.0.0.1:8787/__ready`: 200, `0.003947s`.
- `http://127.0.0.1:13000/`: 200, `1.713448s`.

## Follow-Up

- Treat this as a comparison baseline, not a pass/fail performance budget.
- Next performance task should split server component payload size, API latency, and React render time before tuning.
