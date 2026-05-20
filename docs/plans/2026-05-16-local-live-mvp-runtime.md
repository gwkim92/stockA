# Local Live MVP Runtime Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Prepare a local live MVP runtime path and remove the scheduler exact-command shell blocker.

**Architecture:** Use repo-outside runtime files under `/private/tmp/stockanalysis-runtime`, Python 3.13 venv, FastAPI read-only backend, existing Next.js cockpit, and existing data operations runner. Keep scheduler physical activation outside Codex.

**Tech Stack:** Python 3.13, FastAPI, Uvicorn, psycopg, Next.js, Postgres, launchd command preview only.

---

## Tasks

1. Add task docs and record guardrails.
2. Fix `$HOME` LaunchAgents command preview.
3. Prepare runtime venv and env files outside repo.
4. Run verification and smoke checks.
5. Record handoff with blockers and next action.
