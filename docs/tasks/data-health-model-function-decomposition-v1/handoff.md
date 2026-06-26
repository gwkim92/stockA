# data-health-model-function-decomposition-v1 Handoff

## Status

- status: completed_ec2_smoke_passed
- completed: local typecheck, unit tests, build, frontend contract, roadmap verification, AWH, e2e, local route smoke, visual screenshot QA, diff check, commit, push, EC2 pull, EC2 build, service restart, and route smoke are complete.
- current status: completed.

## Current Finding

UX/UI 정상화 기반 작업은 상당 부분 완료됐지만 `/data-health` 표현 모델은 아직 완료 상태가 아니다. `dataHealthDefaults.ts`와 `dataHealthTypes.ts`가 분리됐음에도 `dataHealthModel.ts`가 1,606줄로 남아 copy, scheduler/runtime, AI/provider, outcome/professional analysis 표현 로직을 함께 소유하고 있다.

## Plan

1. `dataHealthModel.ts`를 compatibility re-export 모듈로 축소한다.
2. 사용자/운영자 문구와 공통 formatter는 `dataHealthCopyModel.ts`로 분리한다.
3. open gate triage는 `dataHealthGateModel.ts`로 분리한다.
4. pipeline run label은 `dataHealthRunModel.ts`로 분리한다.
5. scheduler/timer 표현 로직은 `dataHealthSchedulerModel.ts`로 분리한다.
6. manual smoke, local worker, Toss market data 표현 로직은 `dataHealthRuntimeModel.ts`로 분리한다.
7. AI 품질 감사 표현 로직은 `dataHealthAiQualityModel.ts`로 분리한다.
8. 뉴스 AI eval, live AI invocation, OpenAI provider 표현 로직은 `dataHealthAiProviderModel.ts`로 분리한다.
9. benchmark drift 표현 로직은 `dataHealthBenchmarkModel.ts`로 분리한다.
10. outcome maturity/action router 표현 로직은 `dataHealthOutcomeModel.ts`로 분리한다.
11. professional source/quality/audit 표현 로직은 `dataHealthProfessionalModel.ts`로 분리한다.
12. 검증 후 EC2 `develop`에 배포하고 `13000` route smoke를 확인한다.

## Verification Log

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm test`
- passed: `cd apps/web && npm run build`
- passed: `bash scripts/verify_frontend_api_contract.sh`
- passed: `bash scripts/verify_project_execution_roadmap.sh`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-model-function-decomposition-v1`
- passed: local route smoke against `http://127.0.0.1:13006` for `/`, `/data-health`, `/portfolio/coverage`, `/paper-trading`, `/stocks/AAPL`, `/recommendations/AAPL-2024-11-01`.
- passed: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13006 npm run test:e2e` with 54 tests passed.
- passed: browser screenshot QA for `/data-health` at 375px, 768px, 1280px. Captures are in `output/playwright/data-health-model-function-decomposition-v1/`.
- passed: `git diff --check`
- passed: touched model files are under 250 pure LOC except existing `dataHealthDefaults.ts`, which was not changed in this task.
- passed: local commit `69badcf4` pushed to `origin/develop`.
- passed on EC2: `/opt/stockanalysis/app` fast-forwarded to `69badcf4`.
- passed on EC2: `cd /opt/stockanalysis/app/apps/web && npm run typecheck && npm run build`.
- passed on EC2: `stockanalysis-web.service` and `stockanalysis-frontend-api.service` are `active`.
- passed on EC2: `/`, `/data-health`, `/portfolio/coverage`, `/paper-trading`, `/stocks/AAPL`, `/recommendations/AAPL-2024-11-01` returned `200`.
- passed on EC2: FastAPI `http://127.0.0.1:8787/__ready` returned success.
- passed via local tunnel: `http://127.0.0.1:13000/data-health` returned `200`.

## Exact Next Step

- exact next step: continue with `/data-health/page.tsx` section decomposition or `dataHealthDefaults.ts` domain split if the next task remains operations-console cleanup; otherwise return to investor-page UX issues in recommendation/stock detail.

## Remaining Risk

- `dataHealthDefaults.ts`는 아직 836줄이다. 이번 작업은 function model 분해에 집중하고, defaults 데이터 테이블의 domain split은 별도 후속 작업으로 남긴다.
- `/data-health/page.tsx`는 아직 2,783줄이다. 이번 작업 후에도 route JSX section decomposition은 계속 남는다.
