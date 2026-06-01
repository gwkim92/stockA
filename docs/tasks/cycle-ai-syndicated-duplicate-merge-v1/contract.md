# cycle-ai-syndicated-duplicate-merge-v1 Contract

## Task Request

- request: Close the remaining `cycle_ai_quality_audit_attention` gate without hiding the duplicate news warning.
- context: EC2 `/api/data-health` reports one duplicate RSS title: `Here’s the real story behind the record drop in America’s oil reserves`.

## Goal

- goal: Merge safe syndicated duplicate RSS documents/events into one canonical event so the same article does not double-count AI evidence, propagated impacts, or data-health quality issues.

## Root Cause

- The same article entered through two free RSS sources, MarketWatch and Yahoo Finance, with the same title and published timestamp.
- Both rows had downstream event/evidence/impact rows, so the old duplicate cleanup intentionally skipped them because it only deleted empty duplicates.
- This is not a ticker or theme classification bug; it is a syndicated mirror deduplication gap.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/cycle_ai_quality_audit.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `tests/test_cycle_ai_quality_audit.py`
  - `tests/test_operating_data_orchestrator.py`
  - `docs/tasks/cycle-ai-syndicated-duplicate-merge-v1/*`

## Non-Goals

- No recommendation scoring weight changes.
- No broker/order enablement.
- No broad historical AI artifact rewrite beyond safe duplicate merge.
- No deletion of non-duplicate or ambiguous news.

## Safety Policy

- Only merge documents that share normalized title and observed timestamp.
- Keep a canonical event/document and move compatible downstream rows to it.
- Delete conflicting duplicate impact rows only when the canonical event already has the same primary-key impact.
- Move AI artifacts and document chunks to the canonical document/event before deleting duplicate rows.
- Preserve read-only order boundary metadata in cleanup reports.

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cycle_ai_quality_audit tests.test_operating_data_orchestrator -v`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task cycle-ai-syndicated-duplicate-merge-v1`
- EC2: run duplicate cleanup, rerun cycle AI quality audit, inspect `/api/data-health`.
