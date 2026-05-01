# Frontend API Adapter Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** frontend contract examples를 그대로 반환하는 read-only Python adapter를 만들어 UI scaffold가 DB 없이 API-shaped payload로 개발을 시작할 수 있게 한다.

**Architecture:** `docs/api/frontend/contract-index.json`을 source of truth로 사용한다. adapter는 API path를 exact match로 resolution하고 linked example JSON을 반환한다. actual HTTP server, DB query, frontend scaffold는 아직 만들지 않는다.

**Tech Stack:** Python stdlib, JSON contract files, argparse CLI, unittest, Bash verification.

---

### Task 1: Harness

**Files:**
- Create: `docs/tasks/frontend-api-adapter-foundation/contract.md`
- Create: `docs/tasks/frontend-api-adapter-foundation/plan.md`
- Create: `docs/tasks/frontend-api-adapter-foundation/handoff.md`
- Create: `docs/tasks/frontend-api-adapter-foundation/review.md`

**Steps:**
- Scope를 read-only fixture adapter로 제한한다.
- actual API server, DB reads, frontend scaffold는 제외한다.
- 검증 명령을 고정한다.

### Task 2: Python Adapter

**Files:**
- Create: `src/stockanalysis/frontend/__init__.py`
- Create: `src/stockanalysis/frontend/api_adapter.py`
- Modify: `pyproject.toml`

**Steps:**
- contract index loader를 구현한다.
- API path to example resolver를 구현한다.
- CLI command를 구현한다.
- unknown path는 stable error JSON과 non-zero exit code를 반환한다.

### Task 3: Tests And Verification

**Files:**
- Create: `tests/test_frontend_api_adapter.py`
- Create: `scripts/verify_frontend_api_adapter.sh`

**Steps:**
- known path payload resolution을 테스트한다.
- unknown path failure를 테스트한다.
- CLI `list`와 `get` behavior를 테스트한다.
- verification script는 compileall, unittest, contract verify, CLI smoke를 실행한다.

### Task 4: Docs

**Files:**
- Create: `docs/frontend-api-adapter.md`
- Modify: `README.md`
- Modify: `docs/frontend-architecture.md`
- Modify: `docs/frontend-api-contract.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/frontend-api-adapter-foundation/handoff.md`
- Modify: `docs/tasks/frontend-api-adapter-foundation/review.md`

**Steps:**
- adapter purpose, command examples, boundaries, next task를 문서화한다.
- README와 verification plan에 adapter verify를 등록한다.
- task handoff/review에 verification evidence를 남긴다.
