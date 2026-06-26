# data-health-page-section-decomposition-v1 Handoff

## Current Status

- 완료:
  - local implementation and verification are complete.
  - `/data-health` 하단 투자 품질·성과·전문 분석·포트폴리오 검토 상세 JSX를 route-local 컴포넌트로 분리했다.
  - e2e에서 드러난 `/recommendations/AAPL-2024-11-01` fallback symbol 표시 문제와 `/data-health` tablet timestamp overflow를 같이 보정했다.
- 진행 중:
  - commit, push, and EC2 deploy are pending.
- 막힌 점:
  - none.
- branch: `develop`

## Implementation Summary

- `apps/web/src/app/data-health/page.tsx`
  - inline investment-quality details block을 `DataHealthInvestmentQualityDetails`로 이동했다.
  - page route는 상단 command/runtime 조립과 section composition만 남겼다.
- route-local components added under `apps/web/src/app/data-health/_components/`
  - `DataHealthInvestmentQualityDetails.tsx`
  - `DataHealthOutcomeSections.tsx`
  - `DataHealthProfessionalOverviewSections.tsx`
  - `DataHealthProfessionalQualitySection.tsx`
  - `DataHealthProfessionalRecommendationAuditSection.tsx`
  - `DataHealthProfessionalNextActionSection.tsx`
  - `DataHealthProfessionalDepthSections.tsx`
  - `DataHealthBenchmarkDriftSection.tsx`
  - `DataHealthPortfolioReviewHistorySections.tsx`
  - `DataHealthPortfolioReviewCalibrationSection.tsx`
  - `DataHealthPortfolioReviewCadenceSections.tsx`
- copy/presentation hardening
  - 투자자 화면에 남던 raw provider/status/code 표현을 한국어 label mapping으로 보강했다.
  - `/recommendations/AAPL-2024-11-01`처럼 live DB에 없는 e2e fixture id도 URL의 ticker hint를 사용해 `AAPL` 화면으로 표시한다.
  - `.status-rail .rail-cell` 긴 UTC timestamp가 tablet width를 밀어내지 않도록 `overflow-wrap:anywhere`를 적용했다.

## Size Result

- `apps/web/src/app/data-health/page.tsx`: 1,467 pure LOC
- `DataHealthInvestmentQualityDetails.tsx`: 103 pure LOC
- `DataHealthOutcomeSections.tsx`: 238 pure LOC
- `DataHealthProfessionalDepthSections.tsx`: 245 pure LOC
- `DataHealthPortfolioReviewHistorySections.tsx`: 218 pure LOC
- `DataHealthPortfolioReviewCadenceSections.tsx`: 208 pure LOC

## Verification Log

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm test` (`14` files, `36` tests)
- passed: `cd apps/web && npm run build`
- passed: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13007 npm run test:e2e` (`54` tests)
- passed: `bash scripts/verify_frontend_api_contract.sh`
- passed: `bash scripts/verify_project_execution_roadmap.sh`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-page-section-decomposition-v1`
- passed: `git diff --check`
- passed: Playwright screenshot smoke, overflow `0` at `375`, `768`, `1280` for `/data-health`.
- evidence:
  - `/Users/woody/ai/stockanalysis/output/playwright/data-health-page-section-decomposition-v1/data-health-mobile.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/data-health-page-section-decomposition-v1/data-health-tablet.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/data-health-page-section-decomposition-v1/data-health-desktop.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/data-health-page-section-decomposition-v1/recommendation-aapl-mobile.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/data-health-page-section-decomposition-v1/recommendation-aapl-desktop.png`

## Remaining Risk

- `data-health/page.tsx` is still large at 1,467 pure LOC. This slice removed the investment-quality detail block; the upper command center, runtime, and scheduler sections still need future decomposition.
- Some legacy global classes remain in `globals.css`/`workspace-overrides.css`. This task did not migrate the full page to CSS Modules.
- `/recommendations/AAPL-2024-11-01` still receives incomplete live API data, but the user-visible symbol no longer collapses to `UNKNOWN`; deeper fixture-quality cleanup belongs to a separate API fixture task.

## Next Step

- exact next step: commit and push the verified local changes to `develop`, then deploy EC2 with `git pull --ff-only origin develop` and run route smoke.
- After commit/push, deploy `develop` to EC2 with `git pull --ff-only origin develop`, restart FastAPI/Next, and smoke `/`, `/data-health`, `/recommendations/AAPL-2024-11-01`, `/stocks/AAPL`, `/portfolio/coverage`, `/paper-trading`.
