# Thesis Draft Quality Conditions Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve deterministic thesis drafts so each active recommendation gets a more specific thesis summary, entry condition, invalidation condition, and exit rule.

**Architecture:** Keep the existing thesis title identity and verification-compatible invalidation phrase intact. Enhance only deterministic text generation from already-available recommendation, cycle, price, benchmark, and holding-period inputs; do not change schema, scoring, benchmark calculation, LLM behavior, broker/order flow, or scheduler behavior.

**Tech Stack:** Python signal thesis generator, unittest, local live thesis bootstrap, AWH harness.

---

### Task 1: Harness Contract

**Files:**
- Create: `docs/tasks/thesis-draft-quality-conditions/contract.md`
- Create: `docs/tasks/thesis-draft-quality-conditions/handoff.md`
- Create: `docs/tasks/thesis-draft-quality-conditions/review.md`

**Steps:**
- Define this as a deterministic thesis text quality task.
- Exclude scoring formula changes, schema changes, LLM calls, broker/order writes, and scheduler activation.
- Record verification commands and live DB smoke expectations.

### Task 2: Thesis Text Builder

**Files:**
- Modify: `src/stockanalysis/signal/thesis.py`
- Test: `tests/test_thesis_bootstrap.py`

**Steps:**
- Preserve title format: `{symbol} {bucket} thesis via {node_name}`.
- Add helper functions for score, price, return, cycle, benchmark, entry condition, invalidation condition, and exit condition text.
- Keep the exact substring `recommendation score falls below 0.3500` in invalidation conditions for compatibility.
- Include current score, cycle state/score, latest adjusted close, short/medium return, benchmark, and expected holding days in the generated thesis summary.
- Handle missing price features with explicit `unavailable` language.

### Task 3: Live Runtime Update

**Commands:**
- Run targeted unit tests.
- If unit tests pass, rerun local live `thesis-bootstrap` against the existing local DB so the frontend reads the updated thesis text.
- Do not run scheduler activation or host launchctl commands.

### Task 4: Verification

**Commands:**
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_thesis_bootstrap -v`
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter -v`
- Live CLI smoke: `thesis-bootstrap` against `/private/tmp/stockanalysis-runtime/data-operations.env`
- Live API smoke: `/api/theses/AAPL-bootstrap-v1`
- Browser check: `/theses/AAPL-bootstrap-v1`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task thesis-draft-quality-conditions`
- `git diff --check`

### Done Criteria

- Thesis bootstrap still creates and links the same thesis identity.
- Thesis summary and conditions are more specific than the previous generic bootstrap text.
- Missing price feature cases are explicit rather than silent.
- Local live thesis detail shows the improved text.
- Handoff/review contain fresh verification evidence.
