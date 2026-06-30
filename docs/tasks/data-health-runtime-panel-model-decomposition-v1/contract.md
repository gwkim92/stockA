# data-health-runtime-panel-model-decomposition-v1

## Task Request

- request: `/data-health` route에 남은 수집 상태, runtime detail panel, 실행 이력 row 조립 로직을 route 파일 밖 model로 분리한다.

## Goal

- goal: `apps/web/src/app/data-health/page.tsx`가 화면 composition에 집중하도록 줄이고, collection/runtime/execution 표시 모델을 route-local 함수로 이동한다.

## Mutable Surface

- mutable surface: `apps/web/src/app/data-health/page.tsx`
- mutable surface: `apps/web/src/app/data-health/_components/*`
- mutable surface: `docs/tasks/data-health-runtime-panel-model-decomposition-v1/*`

## Non Goals

- non-goal: 백엔드 API DTO 변경
- non-goal: DB schema, 추천 score weight, benchmark, portfolio position 변경
- non-goal: broker/order boundary 또는 scheduler 동작 변경
- non-goal: `/data-health` visual redesign

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm test`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-runtime-panel-model-decomposition-v1`
- verification command: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13004 npm run test:e2e`

## Acceptance Criteria

- acceptance: `collectionStatusCards`와 `overviewCollectionCards` 조립이 별도 model 함수로 이동한다.
- acceptance: `runtimeDetailPanels` 조립이 별도 model 함수로 이동한다.
- acceptance: `executionHistoryRows` 조립이 별도 model 함수로 이동한다.
- acceptance: `/data-health` route smoke와 375px, 768px, 1280px browser QA가 통과한다.
- acceptance: AWH task verify가 통과한다.
