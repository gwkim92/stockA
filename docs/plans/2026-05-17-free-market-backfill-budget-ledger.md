# Free Market Backfill Budget Ledger Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a local operations runner that reads a prioritized watchlist, respects a cross-run daily Alpha Vantage request ledger, and invokes the existing market price batch upsert only for the remaining free-tier budget.

**Architecture:** Keep product logic in Python backend code under `stockanalysis.operations`, not shell scripts. The runner owns watchlist selection and ledger persistence; the existing ingest batch upsert owns provider fetch, throttle spacing, and Postgres price writes. Ledger/watchlist files stay outside the repository to avoid committing runtime state.

**Tech Stack:** Python stdlib CSV/JSON/pathlib, existing `RuntimeConfig`, existing `run_market_price_batch_upsert`, `stockanalysis-operations` CLI, unittest.

---

### Task 1: Watchlist And Ledger Module

**Files:**
- Create: `src/stockanalysis/operations/market_price_free_backfill.py`
- Test: `tests/test_market_price_free_backfill.py`

**Steps:**

1. Add tests for CSV watchlist parsing:
   - accepts `symbol` header.
   - uppercases symbols.
   - de-duplicates while preserving order.
   - rejects missing/empty symbol rows.
2. Add tests for empty and pre-used ledger behavior:
   - missing ledger means zero used requests.
   - existing ledger for provider/day reduces remaining budget.
3. Implement dataclasses and helpers:
   - `WatchlistSymbol`
   - `load_market_price_watchlist`
   - `load_budget_ledger`
   - `resolve_daily_budget_state`
   - `write_budget_ledger`
4. Run:
   - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_market_price_free_backfill -v`

### Task 2: Free Backfill Runner

**Files:**
- Modify: `src/stockanalysis/operations/market_price_free_backfill.py`
- Test: `tests/test_market_price_free_backfill.py`

**Steps:**

1. Add tests where remaining budget is zero:
   - `run_market_price_free_backfill` returns `status=no_budget`.
   - patched `run_market_price_batch_upsert` is not called.
   - all watchlist symbols are reported as skipped by daily budget.
2. Add tests where remaining budget is smaller than watchlist:
   - runner calls batch upsert with all watchlist symbols and `max_requests_per_run=remaining_budget`.
   - ledger increments by returned `provider_request_count`.
   - result exposes `budget_remaining_before` and `budget_remaining_after`.
3. Implement `run_market_price_free_backfill`.
4. Run:
   - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_market_price_free_backfill -v`

### Task 3: Operations CLI

**Files:**
- Modify: `src/stockanalysis/operations/cli.py`
- Test: `tests/test_data_operations_cli.py`

**Steps:**

1. Add CLI parser command `market-price-free-backfill-run`.
2. Require:
   - `--watchlist`
   - `--ledger`
   - `--env-file` optional.
3. Add options:
   - `--daily-budget` default `25`
   - `--max-requests-per-run` default `25`
   - `--throttle-seconds` default `1`
   - `--fixtures-dir`
   - `--outputsize`
   - `--budget-date`
   - `--repo-root`
4. Use existing path policy to require watchlist and ledger outside the repository.
5. Merge `--env-file` into process env only for the runner call so `RuntimeConfig.from_env()` and `STOCKANALYSIS_ALPHA_VANTAGE_PRICE_MODE` work consistently.
6. Add CLI test that patches runner and asserts parsed arguments.
7. Run:
   - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_data_operations_cli tests.test_market_price_free_backfill -v`

### Task 4: Smoke And Documentation

**Files:**
- Create/modify: `docs/free-market-backfill-budget-ledger.md`
- Modify: `docs/tasks/free-market-backfill-budget-ledger/handoff.md`
- Modify: `docs/tasks/free-market-backfill-budget-ledger/review.md`
- Modify: `docs/tasks/local-live-mvp-runtime/handoff.md`

**Steps:**

1. Create a repo-outside local watchlist under `/private/tmp/stockanalysis-runtime/watchlists/free-market-watchlist.csv`.
2. Run a no-quota smoke with `--max-requests-per-run 0` to verify ledger/report flow without calling provider.
3. Run unit tests and full Python test suite.
4. Run AWH and roadmap verification.
5. Document remaining risks: local-only ledger, provider-side quota mismatch, unadjusted prices.
