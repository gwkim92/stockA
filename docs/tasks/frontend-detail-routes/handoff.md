# Session Handoff

## Active Task

- 이름: frontend-detail-routes
- 담당: Codex
- 날짜: 2026-05-01

## Current Status

- 완료:
  - recommendation/thesis/portfolio coverage detail route를 추가했다.
  - fixture API client와 DTO types를 확장했다.
  - detail route production smoke 검증 스크립트를 추가했다.
- 막힌 점:
  - 현재 없음.

## Files Touched

- 생성:
  - `docs/tasks/frontend-detail-routes/contract.md`
  - `docs/tasks/frontend-detail-routes/plan.md`
  - `docs/tasks/frontend-detail-routes/handoff.md`
  - `docs/tasks/frontend-detail-routes/review.md`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/theses/[thesisId]/page.tsx`
  - `apps/web/src/app/portfolio/coverage/page.tsx`
  - `scripts/verify_frontend_detail_routes.sh`
- 수정:
  - `apps/web/src/app/layout.tsx`
  - `apps/web/src/app/globals.css`
  - `apps/web/src/lib/frontend-api.ts`
  - `apps/web/src/lib/types.ts`
  - `docs/apps-web-scaffold.md`
  - `docs/frontend-architecture.md`
  - `docs/verification-plan.md`

## Decisions

- detail routes are read-only Server Components.
- known fixture ids map directly to current frontend API contract paths.
- no client mutation and no browser-side secrets.

## Verification Already Run

- `bash scripts/verify_frontend_detail_routes.sh`: 통과
- 해당 검증 안에서 `npm run typecheck`, `next build`, fixture server runtime, 신규 detail route production smoke, fixture server regression check가 통과했다.
- `bash -n scripts/verify_frontend_detail_routes.sh`: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-detail-routes`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음

## Still Unverified

- in-app browser visual QA
- AI evidence route

## Exact Next Step

- 다음 세션은 이것부터 시작: in-app browser visual QA를 수행하고 AI evidence/source document route 확장 여부를 결정한다.

## Risks

- fixture ids outside current contract examples return 404 from fixture server.
- browser visual QA는 별도 작업이다.
