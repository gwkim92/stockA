# Frontend API Contract Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** frontend scaffold 전에 daily cockpit, remediation, data health, cycle, recommendation, thesis, portfolio coverage read DTO contract와 example JSON을 고정한다.

**Architecture:** Python/Postgres pipeline을 system of record로 유지하고, frontend는 stable read model DTO만 소비한다. 이번 작업은 actual API server를 만들지 않고 contract index, example payload, verification script를 추가한다.

**Tech Stack:** REST resource contract, JSON examples, Python stdlib JSON validation, Bash verification.

---

### Task 1: Harness

**Files:**
- Create: `docs/tasks/frontend-api-contract-foundation/contract.md`
- Create: `docs/tasks/frontend-api-contract-foundation/plan.md`
- Create: `docs/tasks/frontend-api-contract-foundation/handoff.md`
- Create: `docs/tasks/frontend-api-contract-foundation/review.md`

**Steps:**
- Scope를 frontend API contract와 examples로 제한한다.
- actual API server와 frontend scaffold는 제외한다.
- 검증 명령을 고정한다.

### Task 2: Contract Index And Examples

**Files:**
- Create: `docs/api/frontend/contract-index.json`
- Create: `docs/api/frontend/examples/daily-cockpit.json`
- Create: `docs/api/frontend/examples/remediation-tickets.json`
- Create: `docs/api/frontend/examples/data-health.json`
- Create: `docs/api/frontend/examples/cycle-state-list.json`
- Create: `docs/api/frontend/examples/recommendation-detail.json`
- Create: `docs/api/frontend/examples/thesis-detail.json`
- Create: `docs/api/frontend/examples/portfolio-coverage.json`

**Steps:**
- REST endpoint, method, response DTO, example path를 index에 기록한다.
- 각 example은 `contract_version`, `generated_at`, `data`, `links`를 포함한다.
- examples는 현재 DB schema의 운영 개념을 반영하되 raw table 이름에 의존하지 않는다.

### Task 3: API Contract Doc

**Files:**
- Create: `docs/frontend-api-contract.md`
- Modify: `docs/frontend-architecture.md`

**Steps:**
- contract version, endpoint table, common response conventions, read/write boundary, DTO ownership을 문서화한다.
- frontend architecture의 next task를 contract foundation 완료 상태로 갱신한다.

### Task 4: Verification

**Files:**
- Create: `scripts/verify_frontend_api_contract.sh`
- Modify: `README.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/frontend-api-contract-foundation/handoff.md`
- Modify: `docs/tasks/frontend-api-contract-foundation/review.md`

**Steps:**
- JSON parse와 required fields를 검증한다.
- index endpoint example path가 실제 파일과 일치하는지 검증한다.
- each example top-level contract/version/data/links shape를 검증한다.
- README와 verification plan에 contract를 등록한다.
