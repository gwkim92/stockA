# Review

## Result

- status: completed
- branch: `codex/local-mvp-runtime-aws-bootstrap`
- app commits:
  - `f8d1613 fix: clarify news ai flow wording`
  - `8f34a56 fix: hide evidence search internals`
  - `1b11bf7 fix: simplify evidence source wording`
- scope: frontend wording and information architecture only. No API contract, DB schema, scheduler, data collection, or AI runtime behavior changed.

## What Changed

- `/intelligence` now presents the news flow as `원문 수집 → 1차 분류 → Codex OAuth 분석 → 검증 통과/차단 → 추천 근거 연결`.
- News cluster cards now explain grouping basis, direct stock relation, recommendation usage, representative news, and source evidence in user-facing Korean.
- `/events` now reads as a collected-news screen instead of an internal ledger screen.
- `/ai-evidence/[id]` no longer exposes `validator`, `LLM`, `품질 관문`, `검색/RAG`, or `문서 조각` terminology in the visible user path.
- Evidence-source status now uses `원문 근거 연결` and `원문 근거 N개 연결`.

## Verification

- `git diff --check`: passed.
- `cd apps/web && npm run typecheck`: passed.
- `cd apps/web && npm run build`: passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task news-ai-flow-clarity-pass`: passed.
- EC2 deployment: `/opt/stockanalysis/app` reset to `1b11bf7`; `stockanalysis-frontend-api.service` and `stockanalysis-web.service` active.
- EC2 route smoke passed for `/intelligence?refresh=1b11bf7`, `/events?refresh=1b11bf7`, `/ai-evidence/ai-evidence-248?refresh=1b11bf7`.
- Playwright snapshot for `/intelligence?refresh=1b11bf7` confirmed the visible flow and wording.

## Remaining Risks

- The page still relies on existing data quality. If upstream classification links a news item to the wrong theme or symbol, the screen will now expose that more clearly but does not correct it.
- `/stocks/[symbol]`, `/recommendations/[id]`, and `/paper-trading` still need the same user-facing review pass so stock impact, recommendation evidence, thesis review, and paper-trading status are understandable end to end.
