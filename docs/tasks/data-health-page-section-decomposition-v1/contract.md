# data-health-page-section-decomposition-v1 Contract

## Task Request

- request: `/data-health` UX 정상화가 끝났는지 계속 확인하고, 아직 큰 route 파일로 남은 수정 포인트를 찾아 진행한다.

## Goal

- goal: `apps/web/src/app/data-health/page.tsx`에 남아 있는 대형 투자 품질·성과·전문 분석·포트폴리오 검토 상세 JSX를 route-local 컴포넌트로 분리한다. 화면 문구와 백엔드 DTO, DB schema, 추천 점수, scheduler, AI 분석 로직, broker/order boundary는 변경하지 않는다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/app/data-health/_components/DataHealthInvestmentQualityDetails.tsx`
  - `apps/web/src/app/data-health/_components/DataHealthOutcomeSections.tsx`
  - `apps/web/src/app/data-health/_components/DataHealthProfessional*Section*.tsx`
  - `apps/web/src/app/data-health/_components/DataHealthPortfolioReview*Section*.tsx`
  - `apps/web/src/lib/frontend-api.ts`
  - user-facing copy/presentation files touched only to keep existing e2e hard gates green.
  - `docs/tasks/data-health-page-section-decomposition-v1/*`

## Non Goals

- 백엔드 DTO 변경 금지
- DB schema 변경 금지
- 추천 weight, benchmark, portfolio position 변경 금지
- scheduler cadence 또는 AI 분석 로직 변경 금지
- 실거래 broker submit 구현 금지
- 새 시각 디자인 도입 금지

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm test`
- verification command: `cd apps/web && npm run build`
- verification command: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:<local-port> npm run test:e2e`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-page-section-decomposition-v1`
- verification command: `git diff --check`
- verification command: Playwright screenshot smoke for `/data-health` at 375px, 768px, 1280px.

## Acceptance Criteria

- `/data-health/page.tsx` no longer owns the full investment-quality details JSX.
- Extracted components are route-local and preserve rendered content.
- `/recommendations/AAPL-2024-11-01` fallback route keeps the symbol visible instead of degrading the whole screen to `UNKNOWN`.
- Typecheck, tests, build, e2e, frontend contract, roadmap, AWH verify pass.
- EC2 `develop` deploy and `http://127.0.0.1:13000/data-health` smoke pass.
