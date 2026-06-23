# TossInvest Market Data Agent Context V1 Handoff

## Status

- completed: TossInvest market data snapshots, provider comparison, AI agent Postgres context, paper/live API separation, data-health visibility, and stock-detail candlestick UI are implemented on branch `codex/tossinvest-market-data-agent-context-v1`.
- completed: Task-specific backend, CLI, scheduler, frontend adapter, migration, contract, typecheck, and build verification passed.
- in progress: Full repository `unittest discover` is still blocked by local Python environment issues unrelated to this task.

## Current Decisions

- `market.daily_price_bar` remains canonical and now carries provider provenance.
- Toss KR candles can populate canonical daily bars; Toss US candles remain shadow provider evidence until a future promotion gate.
- AI agents read `stockanalysis.ai.market_context` Postgres read models only; they do not call TossInvest HTTP.
- Recommendation/scoring context excludes Toss live account data by default.
- `/api/paper-trading/preview` represents simulated paper validation for `Long Term Paper`.
- `/api/trading/readiness` represents Toss live account read-only state and disabled submit adapter status.
- Toss order submit, modify, cancel, and mutation paths remain disabled.

## Verification Already Run

- `bash scripts/verify_tossinvest_market_data_agent_context.sh` passed.
- `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter tests.test_frontend_api_adapter` passed.
- `bash scripts/verify_frontend_api_contract.sh` passed.
- `cd apps/web && npm run typecheck` passed after `npm ci`.
- `cd apps/web && npm run build` passed.
- Temporary fixture API plus built Next server route smoke passed for `/stocks/AAPL` and `/data-health`.
- `bash scripts/verify_migrations.sh` passed and applied migrations through `0034_tossinvest_market_data_agent_context.sql`.
- `PYTHONPATH=src python3 -m unittest` ran 0 tests and exited 5 because this repo requires explicit discovery.
- `PYTHONPATH=src python3 -m unittest discover -s tests` ran 1247 tests and failed due local environment issues:
  - Python 3.14 `pyexpat` dylib mismatch breaks XML parsing tests for XLSX/RSS.
  - `fastapi` is not installed for `tests/test_frontend_api_server.py`.
  - News RSS runner failures are downstream of the XML parser failure.

## Residual Risk

- No live Toss credential/API smoke was run from this worktree.
- KR schedules are represented as operating profiles and cadence metadata; actual systemd timezone deployment should be checked on EC2 before activation.
- `npm ci` reported existing npm audit findings: 1 moderate and 1 high vulnerability. Dependency remediation is outside this task.

## Exact Next Step

- exact next step: Review this branch diff, run the task-specific verify script on the intended Python runtime, then merge to `develop` and deploy/smoke only from `develop` if approved.
