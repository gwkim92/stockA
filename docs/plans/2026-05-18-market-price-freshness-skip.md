# Market Price Freshness Skip Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Prevent free market data provider calls when canonical daily prices are already fresh enough.

**Architecture:** Add a small DB freshness lookup before provider payload loading in the existing batch upsert path. Keep it explicit and provider-neutral, then pass the option through CLI and operations runner boundaries.

**Tech Stack:** Python stdlib, existing `PsqlCommandExecutor`, existing market price ingest and operations CLI modules, unittest.

---

### Task 1: Freshness Lookup

**Files:**
- Modify: `src/stockanalysis/ingest/market/price.py`
- Test: `tests/test_market_price.py`

**Step 1:** Add a failing test where a symbol has latest `market.daily_price_bar.trade_date` greater than or equal to target date.

**Step 2:** Implement a helper that returns latest trade date for a symbol or `None`.

**Step 3:** Verify the helper preserves non-missing DB errors.

### Task 2: Batch Skip

**Files:**
- Modify: `src/stockanalysis/ingest/market/price.py`
- Test: `tests/test_market_price.py`

**Step 1:** Add a test proving `run_market_price_batch_upsert(..., skip_if_fresh=True)` skips fresh symbols before provider loading.

**Step 2:** Add skipped result metadata with `reason=fresh_price_data_exists`.

**Step 3:** Ensure provider request budget is not consumed by skipped symbols.

### Task 3: CLI And Operations Propagation

**Files:**
- Modify: `src/stockanalysis/ingest/market/backfill.py`
- Modify: `src/stockanalysis/ingest/cli.py`
- Modify: `src/stockanalysis/operations/market_price_free_backfill.py`
- Modify: `src/stockanalysis/operations/cli.py`
- Test: `tests/test_market_backfill.py`
- Test: `tests/test_ingest_cli.py`
- Test: `tests/test_market_price_free_backfill.py`
- Test: `tests/test_data_operations_cli.py`

**Step 1:** Add `--skip-if-fresh` and `--freshness-date YYYY-MM-DD`.

**Step 2:** Pass values through all existing backend boundaries.

**Step 3:** Add tests for propagation and ledger accounting.

### Task 4: Verification And Handoff

**Files:**
- Modify: `docs/tasks/market-price-freshness-skip/handoff.md`
- Modify: `docs/tasks/market-price-freshness-skip/review.md`
- Modify: `docs/tasks/local-live-mvp-runtime/handoff.md`

**Step 1:** Run focused unittest.

**Step 2:** Run AWH verification.

**Step 3:** Run `git diff --check`.
