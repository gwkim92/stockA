# Market Price Scheduler Approval Packet Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a human-readable approval packet for `market-price-daily` scheduler activation without writing LaunchAgents or running `launchctl`.

**Architecture:** Reuse the existing repo-outside operator dry-run evidence under `/private/tmp/stockanalysis-runtime/evidence/activation-chain-market-price-daily`. Produce a repo documentation packet that lists the exact host commands, rollback commands, current blocker, and the explicit approval record shape. No production env values or API keys are copied into the repo.

**Tech Stack:** Markdown docs, existing data-operations scheduler evidence, Agent Work Harness task contract.

---

### Task 1: Capture Current Evidence State

**Files:**
- Read: `/private/tmp/stockanalysis-runtime/evidence/activation-chain-market-price-daily/pending-approval-gate.json`
- Read: `/private/tmp/stockanalysis-runtime/evidence/activation-chain-market-price-daily/operator-dry-run/evidence/operator-dry-run.json`
- Read: `/private/tmp/stockanalysis-runtime/evidence/activation-chain-market-price-daily/operator-dry-run/rendered/com.stockanalysis.data-operations.market-price-daily.manifest.json`

**Step 1:** Confirm `approval_gate=blocked_pending_manual_approval`.

**Step 2:** Confirm `launchctl_executed=false` and `host_install_path_written=false`.

**Step 3:** Extract rendered plist path, label, schedule, and command argv from the dry-run manifest.

### Task 2: Write Approval Packet

**Files:**
- Create: `docs/market-price-scheduler-approval-packet.md`

**Step 1:** Document current status in plain Korean.

**Step 2:** List exact execution command preview.

**Step 3:** List exact rollback command preview.

**Step 4:** Include an approval record template that the operator can review.

**Step 5:** Explicitly state that this packet does not execute host mutation.

### Task 3: Record Harness Task State

**Files:**
- Create: `docs/tasks/market-price-scheduler-approval-packet/contract.md`
- Create: `docs/tasks/market-price-scheduler-approval-packet/handoff.md`
- Create: `docs/tasks/market-price-scheduler-approval-packet/review.md`

**Step 1:** Define mutable surface.

**Step 2:** Record verification commands.

**Step 3:** Record exact next step for actual host activation.

### Task 4: Verify

**Commands:**
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task market-price-scheduler-approval-packet`
- `git diff --check`

**Expected:** Both pass. No `launchctl` command is executed.
