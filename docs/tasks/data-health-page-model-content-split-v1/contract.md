# data-health-page-model-content-split-v1

## Task Request

- request: `/data-health/page.tsx`에 남은 page-level 데이터 준비와 JSX composition을 route-local model/content 파일로 분리한다.

## Goal

- goal: `apps/web/src/app/data-health/page.tsx`가 `getDataHealth()` 호출과 `DataHealthPageContent` 렌더링만 담당하도록 축소한다.
- goal: 데이터 기본값 보정, 실행 상태 파생, 표시 props 조립은 route-local model 함수로 이동한다.

## Mutable Surface

- mutable surface: `apps/web/src/app/data-health/page.tsx`
- mutable surface: `apps/web/src/app/data-health/_components/*`
- mutable surface: `docs/tasks/data-health-page-model-content-split-v1/*`

## Non Goals

- non-goal: 백엔드 API DTO 변경
- non-goal: DB schema 변경
- non-goal: 추천 score weight, benchmark, portfolio position 변경
- non-goal: broker/order boundary 또는 scheduler 동작 변경
- non-goal: `/data-health` 시각 디자인 변경

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm test`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-page-model-content-split-v1`
- verification command: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13005 npm run test:e2e`

## Acceptance Criteria

- acceptance: `page.tsx`는 data fetch와 model/content 연결만 담당한다.
- acceptance: page model 파일은 `/data-health` 화면에 필요한 view props를 만든다.
- acceptance: content component는 model을 받아 기존 화면 순서대로 렌더링한다.
- acceptance: 주요 변경 파일은 250 pure LOC 기준을 넘지 않는다.
- acceptance: `/data-health` route smoke와 375px, 768px, 1280px browser QA가 통과한다.
- acceptance: AWH task verify가 통과한다.
