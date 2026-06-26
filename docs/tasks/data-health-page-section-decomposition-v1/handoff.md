# data-health-page-section-decomposition-v1 Handoff

## Current Status

- 완료:
  - local implementation and verification are complete.
  - local commit `28844f24` was pushed to `origin/develop`.
  - EC2 `/opt/stockanalysis/app` fast-forward pulled `develop` to `28844f24`.
  - follow-up commit `a186add0` was pushed to `origin/develop` and EC2 fast-forward pulled it.
  - EC2 was recovered after the interrupted `next build`: personal AWS account `115623963546` was verified in Chrome, the instance was rebooted, then stopped/started when SSH remained stuck at banner exchange.
  - EC2 public IPv4 changed from `34.206.72.213` to `100.58.167.160`.
  - EC2 production build was regenerated successfully with temporary swap under `/opt/stockanalysis/runtime`, then swap was removed.
  - EC2 `stockanalysis-web.service` and `stockanalysis-frontend-api.service` are both active.
  - `/data-health` 하단 투자 품질·성과·전문 분석·포트폴리오 검토 상세 JSX를 route-local 컴포넌트로 분리했다.
  - e2e에서 드러난 `/recommendations/AAPL-2024-11-01` fallback symbol 표시 문제와 `/data-health` tablet timestamp overflow를 같이 보정했다.
- 진행 중:
  - none.
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
- passed: `git commit -m "Split data health detail sections"` created `28844f24`.
- passed: `git push origin develop` updated GitHub `develop` from `521830ef` to `28844f24`.
- passed: EC2 `git pull --ff-only origin develop` updated `/opt/stockanalysis/app` to `28844f24`.
- blocked: EC2 `cd /opt/stockanalysis/app/apps/web && npm run typecheck && npm run build` passed typecheck and compiled Next successfully, then stalled during the build TypeScript/route phase until SSH and HTTP became unresponsive.
- passed: EC2 recovery through AWS Console personal account `115623963546`; new public IPv4 is `100.58.167.160`.
- passed: EC2 `npm run build` completed after enabling temporary 2GB swap under `/opt/stockanalysis/runtime`; swap was removed after build.
- passed: EC2 `systemctl is-active stockanalysis-frontend-api.service stockanalysis-web.service` returned `active active`.
- passed: EC2 localhost route smoke returned `200` for `/`, `/data-health`, `/recommendations/AAPL-2024-11-01`, `/stocks/AAPL`, `/portfolio/coverage`, `/paper-trading`, and API `__ready`.
- passed: local tunnel `http://127.0.0.1:13000` returned `200` for `/`, `/data-health`, `/recommendations/AAPL-2024-11-01`, `/stocks/AAPL`, `/portfolio/coverage`, `/paper-trading`.
- passed: Playwright Chrome visual smoke captured `/data-health`, `/recommendations/AAPL-2024-11-01`, and `/stocks/AAPL` with Korean body text and no `pipeline|runner|artifact|canonical|shadow` matches in the captured body text.
- evidence:
  - `/Users/woody/ai/stockanalysis/output/playwright/ec2-recovery-ux-smoke-v1/data-health.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/ec2-recovery-ux-smoke-v1/recommendations_AAPL-2024-11-01.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/ec2-recovery-ux-smoke-v1/stocks_AAPL.png`
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
- `/stocks/AAPL` full-page visual smoke shows the page is still very long and appears to repeat top-level analysis sections near the bottom. This is not a server outage, but it should be handled in the next stock-detail UX decomposition task.

## Next Step

- exact next step: continue the UX normalization with stock-detail duplication/length cleanup, starting from `/stocks/AAPL` and ETF/company layout boundaries.
