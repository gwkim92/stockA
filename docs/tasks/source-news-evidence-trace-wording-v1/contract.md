# source-news-evidence-trace-wording-v1 Contract

## Task Request

- request: Continue the UX wording cleanup on source news and AI evidence trace routes.
- context: Stock and recommendation detail pages were clarified, but source/news routes still contain ambiguous wording such as `AI 판단`, `검토서`, `검수`, `보유검토`, `페이퍼`, and `AI 증거`.

## Goal

- goal: Make `/events`, `/events/classification`, `/source-documents/[documentId]`, and `/ai-evidence/results` read as a clear evidence pipeline: source news -> first-pass tags -> AI evidence -> validator-passed structured result -> recommendation boundary.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/events/page.tsx`
  - `apps/web/src/app/events/classification/page.tsx`
  - `apps/web/src/app/source-documents/[documentId]/page.tsx`
  - `apps/web/src/app/ai-evidence/results/page.tsx`
  - `apps/web/src/components/news-event-card.tsx`
  - `docs/tasks/source-news-evidence-trace-wording-v1/*`

## Invariants

- Do not change API DTO contracts.
- Do not change scheduler cadence.
- Do not change recommendation scoring weights.
- Do not change benchmark definitions, portfolio positions, recommendations, theses, or paper outcomes.
- Do not enable broker submit, automatic orders, or automatic rebalancing.

## Scope

- Replace `AI 판단` with `AI 근거` or `AI 구조화`.
- Replace document/evidence `검토` labels with `근거`, `확인`, or `대조`.
- Replace `보유검토` with `보유 상태`.
- Replace `페이퍼` with `가상 매매`.
- Keep validator and order-boundary language explicit.

## Verification

- verification command: `rg -n "AI 판단|검토서|검수|보유검토|페이퍼|AI 증거|AI 후보|AI 분석 전|추천 승인" apps/web/src/app/events/page.tsx apps/web/src/app/events/classification/page.tsx apps/web/src/app/source-documents/[documentId]/page.tsx apps/web/src/app/ai-evidence/results/page.tsx apps/web/src/components/news-event-card.tsx`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: route smoke for `/events`, `/events/classification`, `/ai-evidence/results`, and a representative source document route.
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task source-news-evidence-trace-wording-v1`
