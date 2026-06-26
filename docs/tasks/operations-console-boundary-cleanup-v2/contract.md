# operations-console-boundary-cleanup-v2 Contract

## Task Request

- request: `/data-health`의 남은 대형 route 책임을 줄이고 운영 콘솔 전용 컴포넌트 경계를 강화한다.
- request: 투자자 화면과 운영 콘솔 경계를 유지하면서 `/data-health/page.tsx`의 helper/default/model 블록과 반복 details/section JSX를 route-local component로 이동한다.

## Goal

- goal: `/data-health/page.tsx`가 API DTO 해석, 기본값 선택, 핵심 view-model 조립, section composition에 집중하게 만든다.
- goal: 운영 콘솔의 반복 UI는 `apps/web/src/app/data-health/_components/`로 이동한다.
- goal: 투자자 화면에서 금지한 내부 용어 노출을 재발시키지 않는다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/app/data-health/_components/**`
  - `apps/web/src/components/operations/DataHealthOverview.tsx`
  - `apps/web/src/components/research/PageDecisionMap.tsx`
  - `apps/web/src/components/research/PageDecisionMap.module.css`
  - `apps/web/src/app/globals.css`
  - `apps/web/src/styles/workspace-overrides.css`
  - `docs/tasks/operations-console-boundary-cleanup-v2/**`

## Non-goals

- 백엔드 DTO, DB schema, 추천 점수, benchmark, portfolio position, broker/order boundary는 변경하지 않는다.
- 스케줄러 주기, 데이터 수집 cadence, AI 분석 로직은 변경하지 않는다.
- `/data-health`의 모든 세부 섹션을 이번 패스에서 완전 분해하지 않는다.

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm test`
- verification command: `cd apps/web && npm run build`
- verification command: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13003 npm run test:e2e`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task operations-console-boundary-cleanup-v2`
