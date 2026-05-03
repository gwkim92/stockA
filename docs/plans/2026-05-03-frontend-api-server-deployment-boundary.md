# Frontend API Server Deployment Boundary Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** FastAPI read-only frontend API server의 배포 topology, process boundary, reverse proxy/TLS assumptions, runtime env readiness gate를 고정한다.

**Architecture:** 실제 host service install, reverse proxy config, TLS certificate, secret file은 생성하지 않는다. 대신 repo 밖 env template, preflight checker, env-based run wrapper, verification script, deployment boundary 문서를 추가한다.

**Tech Stack:** Bash, Python stdlib validation, FastAPI server CLI, AWH task harness.

---

### Task 1: Lock Task Contract

**Files:**
- Create: `docs/tasks/frontend-api-server-deployment-boundary/contract.md`
- Create: `docs/tasks/frontend-api-server-deployment-boundary/plan.md`
- Create: `docs/tasks/frontend-api-server-deployment-boundary/handoff.md`
- Create: `docs/tasks/frontend-api-server-deployment-boundary/review.md`

**Steps:**
1. Define the deployment boundary as documentation plus safe runtime env tooling.
2. Exclude service manager install, reverse proxy config writes, TLS material, full auth/RBAC, write APIs, schema/scoring changes.
3. List verification commands.

### Task 2: Add Runtime Env Template Renderer

**Files:**
- Create: `scripts/render_frontend_api_server_env_template.sh`

**Steps:**
1. Require `--output PATH`.
2. Refuse output inside the repository.
3. Render shell-sourceable env placeholders for FastAPI server production profile.
4. Set file mode to `600`.

### Task 3: Add Runtime Env Readiness Checker

**Files:**
- Create: `scripts/check_frontend_api_server_runtime_env.sh`

**Steps:**
1. Require `--env-file PATH`.
2. Refuse env files inside the repository.
3. Source the trusted env file.
4. Validate required values, placeholder removal, loopback bind host, positive port, production/read-token profile, explicit HTTPS allowed origin, DB URL shape, token length, pool sizes, request timeout.
5. Print safe JSON summary without DB URL or token.

### Task 4: Add Env-Based Run Wrapper

**Files:**
- Create: `scripts/run_frontend_api_server.sh`

**Steps:**
1. Accept `--env-file PATH`.
2. Run the readiness checker first.
3. Support `--preflight-only`.
4. Execute `python -m stockanalysis.frontend.api_server` with env-derived host, port, source, runtime profile, auth, pool, timeout, and optional repo root.

### Task 5: Add Verification Script

**Files:**
- Create: `scripts/verify_frontend_api_server_deployment_boundary.sh`

**Steps:**
1. Syntax-check new scripts.
2. Verify repo-internal template output is rejected.
3. Verify unedited template fails readiness.
4. Verify valid temp env passes readiness and wrapper preflight.
5. Verify output JSON redacts DB URL and read token.

### Task 6: Update Docs And Roadmap

**Files:**
- Create: `docs/frontend-api-server-deployment-boundary.md`
- Modify: `README.md`
- Modify: `docs/frontend-api-server.md`
- Modify: `docs/frontend-api-runtime-boundary.md`
- Modify: `docs/frontend-architecture.md`
- Modify: `docs/frontend-runtime-db-smoke.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Modify: `docs/tasks/frontend-api-server-deployment-boundary/handoff.md`
- Modify: `docs/tasks/frontend-api-server-deployment-boundary/review.md`

**Steps:**
1. Document loopback API behind TLS reverse proxy.
2. Document required forwarded headers and cache assumptions.
3. Move immediate next task to frontend API pagination conventions.
4. Record verification evidence.

### Task 7: Verify And Publish

**Commands:**
- `bash scripts/verify_frontend_api_server_deployment_boundary.sh`
- `bash scripts/verify_frontend_api_server.sh`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=src python3 -m unittest discover -s tests`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-server-deployment-boundary`
- `git diff --check`

**Steps:**
1. Run targeted deployment-boundary verification.
2. Run FastAPI server smoke and regression tests.
3. Run roadmap and AWH verification.
4. Commit, push, and open PR.
