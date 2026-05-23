# Review

## Result

- status: completed
- branch: `codex/local-mvp-runtime-aws-bootstrap`
- app commits:
  - `47b97f8 fix: clarify decision detail flows`
  - `738fc14 fix: remove quality jargon from decision pages`
  - `cd33442 fix: simplify stock source evidence wording`
- scope: frontend wording and information architecture only. No API contract, DB schema, recommendation scoring, paper-trading execution, broker boundary, scheduler, or AI runtime behavior changed.

## What Changed

- `/stocks/[symbol]` now avoids ledger/search/indexing jargon and labels source evidence as `원문 근거`.
- Stock detail links now use `수집 뉴스`, `AI 근거`, and `종목 영향` style wording instead of internal event/evidence labels.
- `/recommendations/[id]` now says `중장기 검토 판정`, `근거 연결 점검`, `종목 영향 보기`, and `수집 뉴스 열기`.
- Backend-provided Korean explanations that contained `품질 점검` are translated to user-facing `근거 점검` wording at the label layer.
- `/paper-trading` now labels the side interpretation as `추천 성과 점검` and keeps the screen focused on paper candidates versus actual broker submission.

## Verification

- `git diff --check`: passed.
- `cd apps/web && npm run typecheck`: passed after rerunning separately from `next build`.
- `cd apps/web && npm run build`: passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task decision-detail-flow-clarity-pass`: passed.
- EC2 deployment: `/opt/stockanalysis/app` reset to `cd33442`; `stockanalysis-frontend-api.service` and `stockanalysis-web.service` active.
- EC2 route smoke passed for `/stocks/QUBT?refresh=cd33442`, `/recommendations/recommendation-75?refresh=cd33442`, `/paper-trading?refresh=cd33442`.
- Playwright snapshot text checks passed for the same three routes.

## Remaining Risks

- This pass improves wording and flow only. If upstream classification or recommendation evidence is wrong, the screen now exposes it more clearly but does not repair the data.
- `/data-health`, `/ai-evidence/results`, `/ai-evidence/blocked`, and `/trading-readiness` still need a final user-facing monitoring pass so collection, AI analysis, blocked candidates, and trade readiness feel like one coherent operations console.
