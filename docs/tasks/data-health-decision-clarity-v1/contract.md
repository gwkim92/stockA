# Task Contract

## Task Request

- name: `data-health-decision-clarity-v1`
- request: Improve `/data-health` so the user can quickly understand what is healthy, what is waiting by design, and what needs action.

## Objective

The data-health page has the right operational evidence, but too much of it still reads like logs. The page should first answer whether collection, AI analysis, pricing, alerts, and investment safety boundaries are usable before showing detailed run records.

## Goal

- goal: Add a human-readable operational triage layer to `/data-health`: immediate issues, managed waits, source limits, investment review items, and healthy controls.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/data-health-decision-clarity-v1/*`

## Non-Goals

- Do not change API contracts, DB schema, scheduler behavior, recommendation weights, benchmark definitions, portfolio positions, broker/order flow, or write APIs.
- Do not hide source limits, stale data, managed waits, or attention items.
- Do not turn operational evidence into investment advice.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task data-health-decision-clarity-v1`
- route smoke: `http://127.0.0.1:13000/data-health`
