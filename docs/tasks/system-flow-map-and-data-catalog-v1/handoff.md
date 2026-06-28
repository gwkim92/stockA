# system-flow-map-and-data-catalog-v1 Handoff

## Current Status

- completed: local implementation is complete on `feature/system-flow-data-ai-quality-normalization-v1`; ready for review/merge after final git hygiene.

## Current Decision

- Treat this as a presentation and operating-boundary normalization task.
- Do not add new scoring weights, new paid tools, broker submit, or large schema changes.
- Use existing Postgres/FastAPI/Next/Systemd data and existing DTOs wherever possible.

## Implementation Notes

- System purpose remains: a long-term investment operations system, not a news summary site.
- Fixed flow: `collection -> quality validation -> AI structuring -> cycle/company/ETF analysis -> recommendation/holding/paper validation -> outcome feedback`.
- AI may structure and explain evidence, but deterministic jobs own score, portfolio constraints, paper validation, and order boundary.
- Added `docs/system-flow-map.md` and `docs/data-catalog.md` to make architecture, data-source roles, AI boundary, and zero-weight/blocked evidence explicit.
- Added `/data-health` decision-flow status cards for news/AI, market prices, cross-asset, Toss broker reality, recommendations/holdings, and performance feedback.
- Added data-gap scorecards so missing corporate actions, earnings/guidance, ownership/insider, breadth/credit/liquidity, ETF/fund freshness, and Toss account/fill data are treated as source limits or zero-weight evidence rather than hidden failures.
- Expanded `/admin/ai-agents` with prompt/model/eval runtime visibility: prompt versions, output schemas, fallback policy, recent runtime state, and batch-only AI boundary.
- Expanded `/stocks/[symbol]` header density with analysis price status and Toss broker reality status while keeping company and ETF/fund presentation paths separate.
- Adjusted Playwright coverage for summary-style historical recommendation records so the E2E gate verifies the correct compact summary UX instead of requiring professional-detail-only selectors.
- Added fixture-only visual QA examples for `/stocks/SPY` and `/recommendations/AAPL-professional-2026-06-25` through `src/stockanalysis/frontend/api_adapter.py` without expanding the public `contract-index.json` endpoint count.
- Fixed recommendation position reality copy so raw DTO wording does not leak `확인한다` into investor-facing screens, and missing recommended weight renders as `미측정` instead of `NaN%`.
- Extracted `/data-health` decision-flow and data-gap mapping into `DataHealthDecisionFlowModel` with unit coverage so the large route file no longer owns the new presentation mapping.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm test` (`18 passed`, `42 tests`)
- passed: `cd apps/web && npm run build`
- passed: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13003 npm run test:e2e` (`69 passed`)
- passed: route smoke through Playwright against local `next start` on `127.0.0.1:13003` for `/`, `/data-health`, `/admin/ai-agents`, `/stocks/AAPL`, `/stocks/SPY`, `/recommendations/AAPL-2024-11-01`, `/recommendations/AAPL-professional-2026-06-25`
- passed: visual QA screenshot capture for `/stocks/AAPL`, `/stocks/SPY`, `/data-health`, `/admin/ai-agents`, `/recommendations/AAPL-professional-2026-06-25` at 375px, 768px, and 1280px. Evidence summary is in uncommitted local artifact `apps/test-results/visual-qa-system-flow/summary.json`; every captured route had `overflow=0`, `hasNaN=false`, and `hasErrorState=false`.
- passed: code-review recheck by subagent `019f0a29-4ff2-7370-b132-f31a44de10ec`; blockers closed, only watch item is the still-large legacy `/data-health/page.tsx`.
- note: QA subagent recheck `019f0a2a-1125-7452-8027-9274cb7ed716` could not run because the subagent account hit a usage limit. The same SPY/professional recommendation checks were covered by direct Playwright E2E and screenshot QA above.
- passed: `bash scripts/verify_frontend_api_contract.sh`
- passed: `PYTHONPATH=src python3 -m unittest tests.test_frontend_api_adapter -v`
- passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- passed: `bash scripts/verify_project_execution_roadmap.sh`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task system-flow-map-and-data-catalog-v1`
- passed: `git diff --check`

## Next Step

- exact next step: commit this feature branch, merge to `develop`, then deploy by pulling `develop` on EC2 if deployment access is available.

## Risks

- `/data-health` remains a large file; this task will extract only the new top-level decision-flow/status pieces rather than fully decomposing every legacy detail panel.
- EC2 deployment is separate from local verification and should happen only after merge to `develop`.
- This task does not add new data sources, new prompt content, scoring changes, schema changes, or broker submit. It makes current flow/data/AI boundaries visible and auditable.
