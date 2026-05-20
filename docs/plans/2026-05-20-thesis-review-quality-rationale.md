# Thesis Review Quality Rationale Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make thesis review rows explain why the system chose `watch`, `reduce`, `exit`, or `keep` using recommendation, cycle, price, and missing-data signals.

**Status:** Implemented and locally verified on 2026-05-20. Live AAPL review currently resolves to `exit` from unchanged deterministic inputs: recommendation bucket `avoid`, action `exclude`, score below `0.3500`.

**Architecture:** Preserve the existing deterministic action rule and database schema. Improve only review summary/change notes text and helper structure so downstream portfolio review and the frontend can show human-readable rationale without changing scoring, benchmark, broker/order, LLM, provider, or scheduler behavior.

**Tech Stack:** Python signal thesis review generator, unittest, local live thesis-review CLI smoke, FastAPI/Next read-only frontend.

---

### Task 1: Harness Contract

**Files:**
- Create: `docs/tasks/thesis-review-quality-rationale/contract.md`
- Create: `docs/tasks/thesis-review-quality-rationale/handoff.md`
- Create: `docs/tasks/thesis-review-quality-rationale/review.md`

**Steps:**
- Define this as a deterministic review rationale task.
- Exclude action rule changes, schema changes, scoring changes, LLM calls, broker/order writes, and scheduler activation.
- Record live verification commands.

### Task 2: Review Rationale Helpers

**Files:**
- Modify: `src/stockanalysis/signal/thesis_review.py`
- Test: `tests/test_thesis_review_bootstrap.py`

**Steps:**
- Add helper functions to format score, price, return, cycle, and review rationale.
- Preserve `_review_action()` behavior.
- Generate Korean summary text that includes action, score, bucket/action, cycle state/score, latest close, 1-day return, observation-window return, and next review date.
- Generate change notes listing deterministic triggered signals such as `score_below_threshold`, `recommendation_exclude`, `cycle_structurally_broken`, `market_features_unavailable`.
- Handle missing cycle/price features explicitly.

### Task 3: Documentation

**Files:**
- Modify: `docs/thesis-review-bootstrap.md`

**Steps:**
- Document that the review action rule is unchanged.
- Add an example Korean summary and change notes.

### Task 4: Live Runtime Update

**Commands:**
- Run targeted unit tests.
- Rerun local live `thesis-review-bootstrap` against repo-outside data operations env.
- Do not run scheduler activation or host launchctl commands.

### Task 5: Verification

**Commands:**
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_thesis_review_bootstrap -v`
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter -v`
- local live `thesis-review-bootstrap`
- live API smoke: `/api/theses/AAPL-bootstrap-v1`
- browser smoke: `/theses/AAPL-bootstrap-v1`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task thesis-review-quality-rationale`
- `git diff --check`

### Done Criteria

- Thesis review action behavior remains compatible.
- Review summary/change notes explain the rationale in Korean.
- Missing evidence/data is explicit.
- Local live thesis detail shows the updated review state.
- Handoff/review contain fresh verification evidence.
