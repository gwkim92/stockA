# Data Operations Scheduler Alert Boundary Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add secret-free alert rule references for Data Operations scheduler health before actual scheduler activation.

**Architecture:** A static Prometheus-compatible YAML rule file defines operational alerts. A Python stdlib validator enforces stable alert names, expected metrics, bounded labels, and no receiver/secret tokens. Verification compiles the validator, validates the rule file, and checks docs/roadmap/handoff markers.

**Tech Stack:** YAML text, Python stdlib regex validator, bash verification.

---

### Task 1: Alert Rules

**Files:**
- Create: `ops/observability/data-operations-alert-rules.yml`

**Steps:**
- Add six rules in fixed order.
- Use only documented data operations metrics.
- Include severity, service label, summary, description, and runbook URL.

### Task 2: Validator

**Files:**
- Create: `scripts/validate_data_operations_alert_rules.py`

**Steps:**
- Validate alert order.
- Validate expected metric names.
- Reject receiver/secret/dynamic business identifiers.
- Reject labels outside bounded operational labels.

### Task 3: Verification

**Files:**
- Create: `scripts/verify_data_operations_scheduler_alert_boundary.sh`

**Steps:**
- Check script syntax and validator compile.
- Validate rule file.
- Check docs/task files and roadmap markers.
- Run AWH verify.

### Task 4: Docs And Handoff

**Files:**
- Create: `docs/data-operations-scheduler-alert-boundary.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Modify: task handoff/review.

**Steps:**
- Document alert boundary and future receiver work.
- Move immediate next task after completion.
- Record verification evidence and residual risks.
