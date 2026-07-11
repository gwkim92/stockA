# professional-workspace-cjk-copy-finalization-v1 Contract

## Task Request

- request: Complete the interrupted 2026-07-04 Korean/CJK wrapping cleanup without weakening investment semantics or long-token resilience.
- context: 31 frontend files are modified on top of `817bd3b3`; automated type/test/build checks pass, but the latest independent 375px visual review still reports broken Korean words and phrases.

## Goal

- goal: Finish the interrupted Korean/CJK wrapping cleanup without weakening investment semantics, long-token resilience, or the read-only order boundary.
- Preserve the current UX work, restore the distinctions between news evidence and deterministic cycle evidence, keep the professional-decision boundary explicit, and pass fresh responsive visual QA on every affected route.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/cycle-map/`
  - `apps/web/src/app/recommendations/[recommendationId]/`
  - `apps/web/src/app/stocks/[symbol]/_components/`
  - `apps/web/src/app/globals.css`
  - `apps/web/src/styles/workspace-overrides.css`
  - `apps/web/src/components/recommendation-*`
  - `apps/web/src/components/professional-research-flow*`
  - `apps/web/src/lib/presentation/`
  - `apps/web/tests/e2e/investment-workspace.spec.ts`
  - relevant frontend tests and this task's documents

## Invariants

- Do not change recommendation scoring, component weights, benchmark definitions, portfolio positions, paper-validation decisions, broker integration, or order boundaries.
- Do not merge news evidence and deterministic cycle evidence into a single ambiguous concept.
- Do not replace the specific `professional decision input` boundary with a blanket `analysis input` boundary.
- Do not solve Korean wrapping by removing the emergency break behavior required for long external identifiers, URLs, or source names.
- Do not stage `.omo/`, `apps/test-results/`, `apps/web/test-results/`, or `dogfood-output/` without an explicit artifact-retention decision.

## Acceptance Criteria

- The prior 375px blockers and the latest `위/험을`, `않/는다`, `필/요한`, and `뉴스 흐/름` splits are absent.
- Korean copy uses one consistent sentence-ending register within each panel.
- `/cycle-map`, summary recommendation, professional recommendation, `/stocks/AAPL`, and `/stocks/SPY` pass at 375px, 768px, and 1280px without clipping or horizontal overflow.
- Long unbroken English/source tokens remain contained rather than silently clipped.
- Unit tests, typecheck, production build, full Playwright E2E, frontend API contract, roadmap verification, AWH task verification, and `git diff --check` pass.

## Verification Commands

- verification command: `cd apps/web && npm test`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13003 npm run test:e2e -- --workers=1`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task professional-workspace-cjk-copy-finalization-v1`

```bash
cd /Users/woody/ai/stockanalysis/apps/web
npm test
npm run typecheck
npm run build
STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13003 npm run test:e2e -- --workers=1

cd /Users/woody/ai/stockanalysis
bash scripts/verify_frontend_api_contract.sh
bash scripts/verify_project_execution_roadmap.sh
git diff --check
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task professional-workspace-cjk-copy-finalization-v1
```
