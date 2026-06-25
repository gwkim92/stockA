# data-health-execution-scheduler-section-extraction-v1 Contract

## Task Request

- request: `/data-health` 대형 페이지에서 실행 이력 테이블과 자동화·스케줄러 상세 운영 기록 섹션을 작은 operations component로 분리한다.
- context: `data-health-runtime-detail-panel-extraction-v1`에서 예산·추천 가격·open gate·runtime boundary detail panels를 분리했다. 다음 slice는 남은 실행 이력과 스케줄러 상세 렌더링을 같은 방식으로 추출한다.

## Goal

- goal: 화면 동작과 API DTO를 유지하면서 `/data-health`의 실행 이력과 스케줄러 상세 JSX 책임을 rendering-only operations components로 이동해 `data-health/page.tsx`를 줄이고, 이후 남은 운영자 콘솔 섹션도 작은 단위로 이어서 정리할 수 있게 만든다.

## Mutable Surface

- mutable surface:
  - `docs/tasks/data-health-execution-scheduler-section-extraction-v1/*`
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/app/globals.css`
  - `apps/web/src/components/operations/*`

## Invariants

- Backend DTO, DB schema, provider budget policy, data ingest, AI analysis, recommendation scoring, benchmark, portfolio position을 변경하지 않는다.
- broker submit과 실거래 자동화를 열지 않는다.
- `scheduler-detail`, `execution-log`, `provider-budget`, `active-recommendation-price-freshness`, `runtime-boundary` anchor는 유지한다.
- 새 컴포넌트에는 page에서 만든 한국어 display-ready 값만 넘긴다.

## Scope

- 실행 이력 테이블을 `DataHealthExecutionHistoryPanel`로 분리한다.
- 상세 운영 기록의 자동 반복 실행, 실제 실행 구조, 서버 반복 실행기, 뉴스 분석 이후 운영 흐름, 과거 워커/수동 점검, 자동화 카드 렌더링을 `DataHealthAutomationDetailSection` 계열로 분리한다.
- 컴포넌트 단위 테스트로 주요 한국어 문구와 내부 raw code 미노출을 고정한다.
- 변경은 rendering boundary에 한정한다.

## Verification Commands

- verification command: `cd apps/web && npm test -- --run`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-execution-scheduler-section-extraction-v1`
- verification command: `git diff --check`
- verification command: `Playwright route smoke for http://127.0.0.1:3010/data-health at 375/768/1280px`

## Acceptance Criteria

- `/data-health`는 `작업 실행 이력`, `상세 운영 기록`, `서버 반복 실행기`, `웹 화면은 저장된 결과를 읽고, 서버 예약 작업이 수집·분석을 실행한다`를 계속 렌더링한다.
- 새 component/test files는 250 pure LOC를 넘지 않는다.
- `/data-health` route smoke에서 가로 overflow가 없고 투자 판단 영역 raw code 노출이 늘어나지 않는다.
- 추천 weight, portfolio, benchmark, broker/order boundary가 변경되지 않는다.
