# Frontend Architecture Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 현재 백엔드/파이프라인 중심 프로젝트에 맞는 프론트엔드 구성 원칙, 화면 IA, API 경계, 단계별 구현 순서를 문서화한다.

**Architecture:** 프론트는 추천 결정자가 아니라 투자 운영 cockpit이다. Python/Postgres 파이프라인을 system of record로 유지하고, 웹은 stable read API와 job/action adapter를 통해 cycle, thesis, remediation, performance evidence를 보여준다. 초기에는 앱 scaffold를 만들지 않고 API contract와 화면 구조를 먼저 고정한다.

**Tech Stack:** Next.js App Router + TypeScript proposal, React Server Components by default, Python API adapter, Postgres read models, TanStack Query for client-side server state where needed.

---

### Task 1: Harness

**Files:**
- Create: `docs/tasks/frontend-architecture-foundation/contract.md`
- Create: `docs/tasks/frontend-architecture-foundation/plan.md`
- Create: `docs/tasks/frontend-architecture-foundation/handoff.md`
- Create: `docs/tasks/frontend-architecture-foundation/review.md`

**Steps:**
- Scope를 frontend architecture documentation으로 제한한다.
- actual frontend scaffold는 제외한다.
- 검증 명령을 고정한다.

### Task 2: Frontend Architecture Doc

**Files:**
- Create: `docs/frontend-architecture.md`

**Steps:**
- 현재 frontend가 없다는 사실을 명시한다.
- target user, core workflows, route IA, API boundary, AI role, security boundary를 정의한다.
- 최신 React/Next 방향은 official docs 기준으로 source link를 남긴다.
- 구현 phase와 다음 task를 명확히 적는다.

### Task 3: Verification

**Files:**
- Create: `scripts/verify_frontend_architecture.sh`

**Steps:**
- frontend doc과 task docs가 존재하는지 확인한다.
- frontend doc이 cockpit, route map, API boundary, AI boundary, no-direct-recommendation, implementation phases를 포함하는지 확인한다.
- 아직 frontend app scaffold를 만들지 않았다는 boundary를 확인한다.

### Task 4: Docs Index

**Files:**
- Modify: `README.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/frontend-architecture-foundation/handoff.md`
- Modify: `docs/tasks/frontend-architecture-foundation/review.md`

**Steps:**
- README와 verification plan에 frontend architecture를 추가한다.
- task handoff/review에 verification evidence를 남긴다.
