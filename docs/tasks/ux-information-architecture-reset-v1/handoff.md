# ux-information-architecture-reset-v1 Handoff

## Status

- in progress: first news/AI evidence UX slice deployed; second home/data-health/intelligence slice deployed; third cycle-map/stock-detail/recommendation-detail/paper-trading slice deployed; fourth list/operation slice deployed and verified.

## Current Status

- completed: audited 24 routes through the local EC2 tunnel.
- completed: identified systemic issue: repeated giant hero plus 4-card command panel plus long raw ledger.
- completed: selected first implementation slice: `/events`, `/ai-evidence`, `/ai-evidence/blocked`, `/ai-evidence/results`.
- completed: added compact decision-first layout classes in `apps/web/src/app/globals.css`.
- completed: refactored `/events`, `/ai-evidence`, `/ai-evidence/blocked`, `/ai-evidence/results` so the first viewport shows conclusion, counts, and next action before raw ledgers.
- completed: fixed blocked evidence count confusion by using total blocked/suppressed count in the headline and marking the ledger as latest displayed rows.
- completed: refactored `/`, `/data-health`, `/intelligence` first viewport to use the same decision-first structure.
- completed: refactored `/cycle-map` first viewport around hottest flow, news impact, exposed nodes, and recommendation links.
- completed: refactored `/paper-trading` first viewport to distinguish simulated actions, real order submissions, blocked gates, and hit-rate status.
- completed: refactored `/stocks/[symbol]` first viewport around recommendation, holding, news/flow, and thesis state.
- completed: refactored `/recommendations/[recommendationId]` first viewport around current decision, score, professional step status, paper validation, and live-order boundary.
- completed: removed the unused legacy `StockDecisionBrief` component after replacing it with the shared decision-first layout.
- completed: refactored `/trading-readiness`, `/portfolio/coverage`, `/performance`, `/stocks`, `/recommendations`, `/cycles`, `/events/classification` first viewport to remove repeated page hero/command panel patterns.

## Exact Next Step

- exact next step: deploy the fourth list/operation slice, then audit remaining secondary detail pages such as `/cycles`, `/themes/[themeKey]`, `/theses/[thesisId]`, `/source-documents/[documentId]`, `/remediation`, and lower-fold dense ledgers.

## Risks

- This slice improves information architecture only. It must not change data, scoring, broker/order boundary, or scheduler behavior.
- Dense raw ledgers are still needed for audit; move them below fold rather than deleting evidence.
- Existing top navigation still wraps awkwardly on narrow mobile widths. It did not overflow horizontally, but it needs a separate navigation cleanup slice.
- Raw ledgers are still dense below the fold. They remain intentionally available for audit, but card internals need a later readability pass.

## Verification

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task ux-information-architecture-reset-v1`
- passed: `git diff --check`
- passed locally for third slice: `cd apps/web && npm run typecheck`
- passed locally for third slice: `cd apps/web && npm run build`
- passed locally for third slice: Playwright route smoke on `http://127.0.0.1:3002/cycle-map`, `/stocks/SPY`, `/recommendations/recommendation-67`, `/paper-trading`
- passed locally for third slice: mobile smoke for `/cycle-map`, `/stocks/SPY`, `/recommendations/recommendation-67`, `/paper-trading`, no horizontal overflow at 390px viewport
- passed: local route smoke against EC2 FastAPI tunnel on `http://127.0.0.1:3002/events`, `/ai-evidence`, `/ai-evidence/blocked`, `/ai-evidence/results`
- passed: local route smoke against EC2 FastAPI tunnel on `http://127.0.0.1:3002/`, `/data-health`, `/intelligence`
- passed: mobile smoke for `/events` and `/ai-evidence/blocked`, no horizontal overflow at 390px viewport
- passed: mobile smoke for `/`, `/data-health`, `/intelligence`, no horizontal overflow at 390px viewport
- passed: deployed EC2 tunnel route smoke on `http://127.0.0.1:13000/events`, `/ai-evidence`, `/ai-evidence/blocked`, `/ai-evidence/results`
- passed: deployed EC2 tunnel route smoke on `http://127.0.0.1:13000/`, `/data-health`, `/intelligence`
- deployed commit: `afb64a9`
- deployed commit: `5d2936e`
- passed deployed for third slice: `http://127.0.0.1:13000/cycle-map`, `/stocks/SPY`, `/recommendations/recommendation-67`, `/paper-trading`
- passed deployed for third slice: mobile smoke for `/cycle-map`, `/stocks/SPY`, `/recommendations/recommendation-67`, `/paper-trading`, no horizontal overflow at 390px viewport
- deployed commit: `c814e3f`
- passed locally for fourth slice: `cd apps/web && npm run typecheck`
- passed locally for fourth slice: `cd apps/web && npm run build`
- passed locally for fourth slice: Playwright route smoke on `http://127.0.0.1:3002/trading-readiness`, `/portfolio/coverage`, `/performance`, `/stocks`, `/recommendations`, `/cycles`, `/events/classification`
- passed locally for fourth slice: mobile smoke for the same 7 routes, no horizontal overflow at 390px viewport
- passed deployed for fourth slice: `http://127.0.0.1:13000/trading-readiness`, `/portfolio/coverage`, `/performance`, `/stocks`, `/recommendations`, `/cycles`, `/events/classification`
- passed deployed for fourth slice: mobile smoke for the same 7 routes, no horizontal overflow at 390px viewport
- deployed commit: `6cb23cc`

## Browser Evidence

- desktop screenshot: `/tmp/stockanalysis-ux-reset-v1-after/events.png`
- desktop screenshot: `/tmp/stockanalysis-ux-reset-v1-after/ai-evidence.png`
- desktop screenshot: `/tmp/stockanalysis-ux-reset-v1-after/ai-evidence_blocked.png`
- desktop screenshot: `/tmp/stockanalysis-ux-reset-v1-after/ai-evidence_results.png`
- deployed screenshot: `/tmp/stockanalysis-ux-reset-v1-deployed/events.png`
- deployed screenshot: `/tmp/stockanalysis-ux-reset-v1-deployed/ai-evidence.png`
- deployed screenshot: `/tmp/stockanalysis-ux-reset-v1-deployed/ai-evidence_blocked.png`
- deployed screenshot: `/tmp/stockanalysis-ux-reset-v1-deployed/ai-evidence_results.png`
- local screenshot: `/tmp/stockanalysis-ux-reset-v1-slice2/home.png`
- local screenshot: `/tmp/stockanalysis-ux-reset-v1-slice2/data-health.png`
- local screenshot: `/tmp/stockanalysis-ux-reset-v1-slice2/intelligence.png`
- local mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice2-mobile/home.png`
- local mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice2-mobile/data-health.png`
- local mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice2-mobile/intelligence.png`
- deployed screenshot: `/tmp/stockanalysis-ux-reset-v1-slice2-deployed/home.png`
- deployed screenshot: `/tmp/stockanalysis-ux-reset-v1-slice2-deployed/data-health.png`
- deployed screenshot: `/tmp/stockanalysis-ux-reset-v1-slice2-deployed/intelligence.png`
- mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-mobile/events.png`
- mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-mobile/ai-evidence_blocked.png`
- local screenshot: `/tmp/stockanalysis-ux-reset-v1-slice3-fixed/cycle-map.png`
- local screenshot: `/tmp/stockanalysis-ux-reset-v1-slice3-fixed/stock-spy.png`
- local screenshot: `/tmp/stockanalysis-ux-reset-v1-slice3-fixed/recommendation-67.png`
- local screenshot: `/tmp/stockanalysis-ux-reset-v1-slice3-fixed/paper-trading.png`
- local mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice3-fixed/mobile-cycle-map.png`
- local mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice3-fixed/mobile-stock-spy.png`
- local mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice3-fixed/mobile-recommendation-67.png`
- local mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice3-fixed/mobile-paper-trading.png`
- deployed screenshot: `/tmp/stockanalysis-ux-reset-v1-slice3-deployed/cycle-map.png`
- deployed screenshot: `/tmp/stockanalysis-ux-reset-v1-slice3-deployed/stock-spy.png`
- deployed screenshot: `/tmp/stockanalysis-ux-reset-v1-slice3-deployed/recommendation-67.png`
- deployed screenshot: `/tmp/stockanalysis-ux-reset-v1-slice3-deployed/paper-trading.png`
- deployed mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice3-deployed/mobile-cycle-map.png`
- deployed mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice3-deployed/mobile-stock-spy.png`
- deployed mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice3-deployed/mobile-recommendation-67.png`
- deployed mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice3-deployed/mobile-paper-trading.png`
- local screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4/trading-readiness.png`
- local screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4/portfolio-coverage.png`
- local screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4/performance.png`
- local screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4/stocks.png`
- local screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4/recommendations.png`
- local screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4/cycles.png`
- local screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4/events-classification.png`
- local mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4/mobile-trading-readiness.png`
- local mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4/mobile-portfolio-coverage.png`
- local mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4/mobile-performance.png`
- local mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4/mobile-stocks.png`
- local mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4/mobile-recommendations.png`
- local mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4/mobile-cycles.png`
- local mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4/mobile-events-classification.png`
- deployed screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4-deployed/trading-readiness.png`
- deployed screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4-deployed/portfolio-coverage.png`
- deployed screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4-deployed/performance.png`
- deployed screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4-deployed/stocks.png`
- deployed screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4-deployed/recommendations.png`
- deployed screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4-deployed/cycles.png`
- deployed screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4-deployed/events-classification.png`
- deployed mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4-deployed/mobile-trading-readiness.png`
- deployed mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4-deployed/mobile-portfolio-coverage.png`
- deployed mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4-deployed/mobile-performance.png`
- deployed mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4-deployed/mobile-stocks.png`
- deployed mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4-deployed/mobile-recommendations.png`
- deployed mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4-deployed/mobile-cycles.png`
- deployed mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-slice4-deployed/mobile-events-classification.png`
