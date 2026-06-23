# TossInvest Market Data Agent Context V1 Contract

## Task Request

- request: Implement the approved `Toss Market Data, Agent Context, Paper/Live Split V1` plan.
- request: Separate AI analysis, paper validation, and Toss live read-only account visibility; keep all Toss order submit, modify, and cancel behavior disabled.
- request: Use TossInvest not only for Toss account holdings but as a read-only market data provider evidence layer for all tracked symbols, with KR canonical support and US shadow comparison before promotion.
- request: Add stock detail candlestick chart visibility and show Toss provider source, freshness, and conflict/comparison state.

## Goal

- goal: The service can collect TossInvest read-only market data snapshots, compare Toss shadow prices against canonical daily prices, expose a Postgres-only market context to AI agents, and render stock candles/provider evidence while `broker_submit_allowed=false`, `submitted_to_broker=false`, and `order_boundary=read_only_no_order` remain enforced.

## Scope

- Add TossInvest snapshot tables for daily candles, market calendar, stock warnings, microdata, price limits, and provider comparison.
- Keep `market.daily_price_bar` as canonical, add provider provenance, write Toss KR candles canonically, and keep Toss US candles as shadow evidence.
- Add `stockanalysis-operations tossinvest-market-data-sync-run` and `tossinvest-provider-comparison-run`.
- Add operating-data profiles for KR/US reference, KR/US candles, priority intraday microdata, and live account read-only sync.
- Add an AI market context read model split into canonical market, Toss provider evidence, Toss microdata, paper portfolio, and optional live account read-only sections.
- Add `/api/stocks/{symbol}` fields for `candles`, `market_data_provider`, `toss_provider_evidence`, and `freshness_status`.
- Add `/api/data-health` Toss market data status and provider comparison visibility.
- Add frontend stock-detail SVG candlestick and volume chart with 1M/3M/6M/1Y ranges.
- Clarify `/api/paper-trading/preview` as simulated paper validation and `/api/trading/readiness` as Toss live read-only readiness.

## Non-Goals

- No real Toss order submit, modify, cancel, or order mutation.
- No live order scheduling or broker-side automation.
- No recommendation scoring weight, benchmark, thesis, paper outcome, or performance attribution policy change.
- No canonical promotion of Toss US prices until comparison evidence passes a later explicit gate.
- No AI agent direct Toss HTTP calls.

## Safety Requirements

- Toss secrets and Authorization headers must not appear in logs, reports, API payloads, or tests.
- Live Toss account data must not feed recommendation/scoring agent context by default.
- `Long Term Paper` remains paper validation; `Toss Real Readonly` remains live read-only account visibility.
- All provider conflicts must be surfaced as evidence, not silently guessed away.

## Mutable Surface

- mutable surface:
  - `db/migrations/0034_tossinvest_market_data_agent_context.sql`
  - `src/stockanalysis/operations/tossinvest_market_data.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `src/stockanalysis/operations/operating_data_profile_scheduler.py`
  - `src/stockanalysis/ai/market_context.py`
  - `src/stockanalysis/ingest/market/price.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/app/globals.css`
  - `apps/web/src/components/candlestick-chart.tsx`
  - Toss market data, agent context, scheduler, frontend adapter, and verification tests.
  - `scripts/verify_tossinvest_market_data_agent_context.sh`
  - Task plan, contract, and handoff documents.

Do not mutate recommendation weights, benchmark definitions, paper outcome criteria, broker submit/order mutation endpoints, secrets, deployment settings, or live order boundaries.

## Verification Commands

- verification command: `bash scripts/verify_tossinvest_market_data_agent_context.sh`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_migrations.sh`
- verification command: `PYTHONPATH=src python3 -m unittest`
- verification command: `PYTHONPATH=src python3 -m unittest discover -s tests`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task tossinvest-market-data-agent-context-v1`
