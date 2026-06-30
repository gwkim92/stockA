# data-health-detail-automation-model-decomposition-v1 handoff

## Status

- completed: yes

## Current Scope

- scope: `/data-health` route-local frontend refactor only.
- scope: no schema, scoring, benchmark, portfolio, broker, or scheduler behavior changes.

## Progress

- progress: task contract created.
- progress: moved detail decision card assembly from `page.tsx` into `dataHealthDetailDecisionCardModel.ts`.
- progress: moved portfolio review detail card helpers into `dataHealthDetailPortfolioCardModel.ts`.
- progress: moved automation detail section assembly from `page.tsx` into `dataHealthAutomationDetailModel.ts`.
- progress: moved local worker and manual smoke evidence panels into `dataHealthAutomationEvidencePanelModel.ts`.
- progress: reduced `apps/web/src/app/data-health/page.tsx` from 1,046 to 584 pure LOC in this slice.

## Verification

- verification: `cd apps/web && npm run typecheck` passed.
- verification: `cd apps/web && npm test` passed, 19 files and 45 tests.
- verification: `cd apps/web && npm run build` passed.
- verification: `bash scripts/verify_frontend_api_contract.sh` passed.
- verification: `bash scripts/verify_project_execution_roadmap.sh` passed.
- verification: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-detail-automation-model-decomposition-v1` passed.
- verification: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13004 npm run test:e2e` passed, 69 tests.
- verification: Playwright QA at 375px, 768px, 1280px found horizontal overflow `0`.
- verification: expanded `/data-health` details QA confirmed `세부 판단 카드`, `상세 운영 기록`, `자동 수집 / 분석 상태`, and `뉴스 원문 수집` render.
- verification: screenshots saved under `output/playwright/data-health-detail-automation-model-decomposition-v1/`.
- verification: `git diff --check` passed.

## Remaining Risk

- risk: `apps/web/src/app/data-health/page.tsx` is still a legacy large route at 584 pure LOC.
- risk: next decomposition target is collection status cards, runtime detail panels, and execution history row assembly.

## Exact Next Step

- exact next step: split collection status and runtime detail panel assembly out of `page.tsx` without changing API DTOs or scheduler behavior.
