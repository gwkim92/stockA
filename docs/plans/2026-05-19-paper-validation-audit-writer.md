# Paper Validation Audit Writer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `/api/paper-trading/preview` 결과를 기준으로 `trading.paper_validation_run`과 `trading.order_intent_audit`를 생성하는 broker-free paper audit workflow를 만든다.

**Architecture:** FastAPI frontend API는 계속 read-only로 유지한다. 실제 DB write는 `stockanalysis-operations paper-validation-audit-run` CLI와 `stockanalysis.trading.paper_validation` 모듈에서만 수행한다. Order intent는 기존 deterministic safety evaluator를 통과하며, SQL은 `submitted_to_broker=false`로만 insert/update한다.

**Tech Stack:** Python 3.13, Postgres SQL CTE insert, existing frontend live adapter DTO, existing operations CLI, unittest.

---

## Task 1: Contract

**Files:**
- Create: `docs/tasks/paper-validation-audit-writer/contract.md`
- Create: `docs/tasks/paper-validation-audit-writer/handoff.md`

**Steps:**
- Define boundaries: no broker adapter, no FastAPI write endpoint, no secrets.
- Define verification commands and exact next step.

## Task 2: Writer Module

**Files:**
- Create: `src/stockanalysis/trading/paper_validation.py`
- Modify: `src/stockanalysis/trading/__init__.py`
- Test: `tests/test_trading_paper_validation.py`

**Steps:**
- Build a plan from `PaperTradingPreviewResponse`.
- Derive paper order intents from actionable paper actions.
- Evaluate each intent with `stockanalysis.trading.safety.evaluate_order_intent`.
- Render a single Postgres CTE statement inserting one `paper_validation_run` and zero or more `order_intent_audit` rows.
- Ensure `submitted_to_broker=false` and no `secret_ref` is rendered.

## Task 3: Operations CLI

**Files:**
- Modify: `src/stockanalysis/operations/cli.py`
- Test: `tests/test_data_operations_cli.py`

**Steps:**
- Add `paper-validation-audit-run`.
- Accept `--env-file`, `--as-of-date`, `--portfolio-notional`, `--created-by`, `--human-approved`, and `--dry-run`.
- Read repo-outside env only when provided.
- Print secret-free JSON report.

## Task 4: Docs And Verification

**Files:**
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/paper-validation-audit-writer/handoff.md`

**Commands:**
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_trading_paper_validation tests.test_data_operations_cli tests.test_trading_safety`
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest discover -s tests`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task paper-validation-audit-writer`
- `git diff --check`
