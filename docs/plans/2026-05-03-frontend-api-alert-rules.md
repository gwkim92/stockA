# Frontend API Alert Rules Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a secret-free Prometheus-compatible alert rule reference for the read-only FastAPI frontend API server.

**Architecture:** Keep the application runtime unchanged. Add a repository reference rule file plus a stdlib validator that enforces expected alert names, bounded metric labels, and no receiver or secret content.

**Tech Stack:** Prometheus-compatible alert rule YAML, Python stdlib validation, bash verification, AWH task documents.

---

### Task 1: Create The Task Contract

**Files:**

- Create: `docs/tasks/frontend-api-alert-rules/contract.md`
- Create: `docs/tasks/frontend-api-alert-rules/plan.md`
- Create: `docs/tasks/frontend-api-alert-rules/handoff.md`
- Create: `docs/tasks/frontend-api-alert-rules/review.md`

**Step 1: Define scope**

Document that this slice includes alert rule reference, validation, docs, roadmap, and verification only.

**Step 2: Define exclusions**

Explicitly exclude Alertmanager receivers, contact channel secrets, Collector deployment, write APIs, RBAC, DB schema, scoring, benchmark, and broker/order flow.

**Step 3: Verify files exist**

Run: `test -f docs/tasks/frontend-api-alert-rules/contract.md`

Expected: exit code 0.

### Task 2: Add The Alert Rule Reference

**Files:**

- Create: `ops/observability/frontend-api-alert-rules.yml`

**Step 1: Add the six expected rules**

Rules:

- `FrontendApiDown`
- `FrontendApiNotReady`
- `FrontendApiHigh5xxRate`
- `FrontendApiTimeoutSpike`
- `FrontendApiHighLatency`
- `FrontendApiAdapterErrorSpike`

**Step 2: Keep labels bounded**

Use only static `severity`, static `service`, and bounded PromQL selector labels.

**Step 3: Keep receivers out**

Do not include Slack, email, PagerDuty, OpsGenie, webhook, or other receiver configuration.

### Task 3: Add Rule Validation

**Files:**

- Create: `scripts/validate_frontend_api_alert_rules.py`
- Create: `scripts/verify_frontend_api_alert_rules.sh`

**Step 1: Validate alert order and metrics**

Use Python stdlib parsing to check the six alerts and the expected bounded metric names.

**Step 2: Validate unsafe content**

Fail on receiver strings, auth/secrets, request ids, raw query fields, raw SQL fields, and investment object identifiers.

**Step 3: Run validation**

Run: `bash scripts/verify_frontend_api_alert_rules.sh`

Expected: `frontend API alert rules verification passed`.

### Task 4: Update Roadmap And Handoff

**Files:**

- Create: `docs/frontend-api-alert-rules.md`
- Modify: `docs/frontend-api-observability-sink-decision.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Modify: older frontend API verification scripts that assert immediate next task.

**Step 1: Document the alert boundary**

Explain that the rule file is a reference and not a deployment manifest.

**Step 2: Move the fixed next task**

Set the immediate next task to `data-operations-cadence-foundation`, because API runtime boundary has live reads, FastAPI, SQL pagination, OTLP smoke, and alert references.

**Step 3: Verify roadmap**

Run: `bash scripts/verify_project_execution_roadmap.sh`

Expected: `project execution roadmap verification passed`.

### Task 5: Regression

**Files:**

- Test: `scripts/verify_frontend_api_alert_rules.sh`
- Test: `scripts/verify_project_execution_roadmap.sh`
- Test: `tests/`

**Step 1: Run alert verification**

Run: `bash scripts/verify_frontend_api_alert_rules.sh`

Expected: pass.

**Step 2: Run roadmap verification**

Run: `bash scripts/verify_project_execution_roadmap.sh`

Expected: pass.

**Step 3: Run Python tests**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests`

Expected: pass.

**Step 4: Run AWH**

Run: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task frontend-api-alert-rules`

Expected: pass.
