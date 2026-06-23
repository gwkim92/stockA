# TossInvest Readonly Currency Foundation V1 Contract

## Task Request

- request: Implement the approved `TossInvest Readonly Currency Foundation V1` plan from a synced `develop` base on branch `codex/tossinvest-readonly-currency-foundation-v1`.
- request: Add a read-only TossInvest integration for account, holdings, FX, stock reference, prices, buying power, sellable quantity, and commissions; use KRW as the Toss portfolio base currency; preserve native holding values; expose the read models needed by the cockpit; and add an order adapter stub that never submits, modifies, or cancels broker orders.

## Goal

- goal: A manual TossInvest sync can produce a secret-free report and, when executed, write a separate `Toss Real Readonly` KRW-base portfolio with USD/KRW FX evidence and base/native position values while all order submit/modify/cancel paths remain disabled.

## Scope

- Add TossInvest source request builders for OAuth and read-only account, holdings, FX, stock reference, price, buying power, sellable quantity, and commission endpoints.
- Add `stockanalysis-operations tossinvest-readonly-sync-run` with `--dry-run` and `--execute`.
- Store USD/KRW FX evidence in `market.fx_rate_snapshot`.
- Extend `portfolio.position_snapshot` with nullable native currency and conversion evidence fields.
- Seed Korean market/exchange reference rows.
- Expose Toss sync, currency conversion, and read-only readiness in frontend API read models.
- Add a Toss order adapter stub that raises before any broker HTTP submission.

## Non-Goals

- No scheduler activation.
- No persistent OAuth token cache.
- No Toss order submit, modify, cancel, or order-history mutation.
- No changes to recommendation scoring weights, benchmarks, paper validation outcomes, or broker/order boundary.
- No mutation of `Long Term Paper`; Toss sync writes to `Toss Real Readonly` by default.

## Safety Requirements

- Credentials must come from repo-outside env only.
- Reports, logs, and tests must not expose client secrets, bearer tokens, account numbers, or Authorization headers.
- `broker_submit_allowed=false`, `automatic_order_allowed=false`, and `order_boundary=read_only_no_order` remain enforced.
- Unresolved Toss exchange mappings must be reported in sync output rather than guessed silently.

## Mutable Surface

- mutable surface:
  - `db/migrations/0033_tossinvest_currency_foundation.sql`
  - `db/seeds/0001_reference_seed.sql`
  - `src/stockanalysis/ingest/`
  - `src/stockanalysis/operations/`
  - `src/stockanalysis/trading/tossinvest_order_adapter.py`
  - `src/stockanalysis/performance/coverage.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/`
  - Toss-focused tests, frontend adapter tests, and verification scripts.
  - Task plan, contract, and handoff documents.

Do not mutate recommendation scoring, benchmark definitions, paper validation outcomes, `Long Term Paper` data, broker submit/order endpoints, scheduler activation, secrets, deployment settings, or live order boundaries.

## Verification Commands

- Focused unit and CLI tests for Toss source, normalizer, sync SQL, and order adapter.
- Frontend live/API adapter tests for new read-model fields.
- verification command: `bash scripts/verify_tossinvest_readonly_currency_foundation.sh`
- verification command: `PYTHONPATH=src /tmp/stockanalysis-tossinvest-venv/bin/python -m unittest discover -s tests`
- verification command: `bash scripts/verify_migrations.sh`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task tossinvest-readonly-currency-foundation-v1`
