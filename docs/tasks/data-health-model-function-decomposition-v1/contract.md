# data-health-model-function-decomposition-v1 Contract

## Task Request

- request: `/data-health` UX 정상화 작업이 실제로 끝났는지 확인하고, 부족한 수정 포인트를 찾아 계속 진행한다.

## Goal

- goal: `apps/web/src/app/data-health/_components/dataHealthModel.ts`에 남아 있는 1,600줄 규모의 혼합 표현 로직을 책임별 모듈로 분해한다. 기존 route, API DTO, 화면 문구, 추천 점수, DB schema, scheduler, AI 분석 로직, broker/order boundary는 변경하지 않는다.

## Mutable Surface

- mutable surface:
- `apps/web/src/app/data-health/_components/dataHealthModel.ts`
- `apps/web/src/app/data-health/_components/dataHealthCopyModel.ts`
- `apps/web/src/app/data-health/_components/dataHealthGateModel.ts`
- `apps/web/src/app/data-health/_components/dataHealthRunModel.ts`
- `apps/web/src/app/data-health/_components/dataHealthSchedulerModel.ts`
- `apps/web/src/app/data-health/_components/dataHealthRuntimeModel.ts`
- `apps/web/src/app/data-health/_components/dataHealthAiQualityModel.ts`
- `apps/web/src/app/data-health/_components/dataHealthAiProviderModel.ts`
- `apps/web/src/app/data-health/_components/dataHealthBenchmarkModel.ts`
- `apps/web/src/app/data-health/_components/dataHealthOutcomeModel.ts`
- `apps/web/src/app/data-health/_components/dataHealthProfessionalModel.ts`
  - `docs/tasks/data-health-model-function-decomposition-v1/`

## Non Goals

- 백엔드 DTO 변경 금지
- DB schema 변경 금지
- 추천 weight, benchmark, portfolio position 변경 금지
- scheduler cadence 또는 AI 분석 로직 변경 금지
- 실거래 broker submit 구현 금지
- `/data-health`의 시각 디자인을 새로 갈아엎는 변경 금지

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm test`
- verification command: `cd apps/web && npm run build`
- verification command: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:<local-port> npm run test:e2e`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-model-function-decomposition-v1`
- verification command: `git diff --check`
- verification command: 실제 브라우저 또는 Playwright로 `/data-health`를 375px, 768px, 1280px에서 확인한다.

## Acceptance Criteria

- `dataHealthModel.ts`는 compatibility re-export 경계만 담당한다.
- copy/runtime/AI/outcome 표현 로직이 별도 모듈로 분리된다.
- 기존 import 경로 `./_components/dataHealthModel` 사용자는 깨지지 않는다.
- TypeScript typecheck, build, e2e, frontend contract, roadmap, AWH verify가 통과한다.
- EC2 `develop` 배포 후 `http://127.0.0.1:13000/data-health`가 200으로 열린다.
