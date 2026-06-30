# data-health-detail-automation-model-decomposition-v1

## Task Request

- request: `/data-health` route에 남은 상세 판단 카드와 자동화 상세 조립 로직을 route 파일 밖 route-local model로 분리한다.

## Goal

- goal: 화면 동작과 API DTO를 바꾸지 않고 `apps/web/src/app/data-health/page.tsx`가 데이터 조립과 section composition만 담당하도록 줄인다.

## Mutable Surface

- mutable surface: `apps/web/src/app/data-health/page.tsx`
- mutable surface: `apps/web/src/app/data-health/_components/*`
- mutable surface: `docs/tasks/data-health-detail-automation-model-decomposition-v1/*`

## Non Goals

- non-goal: 백엔드 API DTO, DB schema, 추천 score weight, benchmark, portfolio position, broker/order boundary 변경
- non-goal: `/data-health` 시각 디자인 전면 변경
- non-goal: EC2 systemd scheduler 동작 변경

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm test`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-detail-automation-model-decomposition-v1`
- verification command: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13004 npm run test:e2e`

## Acceptance Criteria

- acceptance: `page.tsx`에서 상세 판단 카드 배열과 자동화 상세 section 조립이 별도 model 함수로 이동한다.
- acceptance: 투자자 화면과 운영 콘솔의 visible copy는 기존과 동일하거나 더 명시적인 한국어 표현을 유지한다.
- acceptance: `/data-health` route smoke와 375px, 768px, 1280px 브라우저 QA가 통과한다.
- acceptance: AWH task verify가 통과한다.
