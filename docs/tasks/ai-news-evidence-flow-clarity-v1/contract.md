# Task Contract

## Task Request

- name: `ai-news-evidence-flow-clarity-v1`
- request: Improve intelligence and AI evidence pages so the user can trace news from collection through AI validation to recommendation linkage.

## Objective

The news/AI pages expose the right data, but the user still has to infer the workflow. The first view should explain where to see raw collected news, first-pass tags, AI candidates, structured results, blocked items, passed items, and recommendation linkage.

## Goal

- goal: Add a clear evidence-flow layer across `/intelligence` and `/ai-evidence` without changing backend contracts.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/intelligence/page.tsx`
  - `apps/web/src/app/ai-evidence/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/ai-news-evidence-flow-clarity-v1/*`

## Non-Goals

- Do not change API contracts, DB schema, AI extraction logic, validator logic, recommendation weights, benchmark definitions, portfolio positions, broker/order flow, or write APIs.
- Do not hide blocked/suppressed evidence.
- Do not claim news/indicator/evidence linkage proves causality or triggers orders.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task ai-news-evidence-flow-clarity-v1`
- route smoke: `http://127.0.0.1:13000/intelligence`
- route smoke: `http://127.0.0.1:13000/ai-evidence`
