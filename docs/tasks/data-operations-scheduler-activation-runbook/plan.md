# Implementation Plan

## Goal

Create the manual activation runbook that must be followed before any actual Data Operations scheduler install.

## Steps

1. [x] Add `docs/data-operations-scheduler-activation-runbook.md`.
2. [x] Add `scripts/verify_data_operations_scheduler_activation_runbook.sh`.
3. [x] Update roadmap, README, verification plan, and AGENTS immediate next task.
4. [x] Update prior data-operations verification scripts to recognize the completed runbook and new next task.
5. [x] Run targeted and full verification.

## Boundary

- This task documents host activation commands but does not execute them.
- This task does not write to `~/Library/LaunchAgents`.
- This task does not run `launchctl`.
- Actual activation remains gated behind explicit manual approval.

## Required Runbook Sections

- Activation boundary
- Required inputs
- Stop conditions
- Preflight sequence
- Manual approval gate
- Activation reference commands
- First-run evidence
- Rollback
- Disable
- Evidence checklist
- Next step
