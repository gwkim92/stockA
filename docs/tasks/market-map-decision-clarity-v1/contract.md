# Task Contract

## Task Request

- name: `market-map-decision-clarity-v1`
- request: Improve `/market-map` so a user can quickly understand what the cross-asset indicators mean for investment review.

## Objective

The market map data is now available and clean, but the page still reads like many repeated indicator cards. The first view should answer: market backdrop, what changed, what to inspect next, and which raw indicator groups support the conclusion.

## Goal

- goal: Reorganize `/market-map` into a clear decision flow: today’s market readout, pressure board, regime signals, compact indicator groups, quality flags, and news linkage.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/market-map/page.tsx`
  - `apps/web/src/app/globals.css`
  - `apps/web/src/lib/korean-labels.ts`
  - `docs/tasks/market-map-decision-clarity-v1/*`

## Non-Goals

- Do not change API contracts, DB schema, cross-asset calculations, recommendation weights, benchmark definitions, portfolio positions, broker/order flow, or write APIs.
- Do not hide stale/missing indicator state.
- Do not claim news/indicator linkage proves causality.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task market-map-decision-clarity-v1`
- route smoke: `http://127.0.0.1:13000/market-map`
