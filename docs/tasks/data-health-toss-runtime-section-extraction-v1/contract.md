# data-health-toss-runtime-section-extraction-v1 Contract

## Task Request

- request: `data-health` 대형 페이지에서 Toss 브로커 현실 데이터와 하단 운영 상세 섹션을 추가로 분리한다.
- context: `frontend-domain-component-extraction-v1`에서 상단 overview/triage/collection 영역을 분리했다. 다음 단계는 Toss 브로커 데이터 section부터 같은 방식으로 추출한다.

## Goal

- goal: Toss 브로커 데이터 section을 rendering-only operations component로 분리해 `data-health/page.tsx`의 책임을 줄이고, Toss 데이터가 “분석 기준 가격”이 아니라 “브로커 현실 확인”이라는 문구를 계속 보존한다.

## Mutable Surface

- mutable surface:
  - `docs/tasks/data-health-toss-runtime-section-extraction-v1/*`
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/components/operations/*`

## Invariants

- Backend DTO, DB schema, Toss ingest, recommendation scoring, benchmark, portfolio position, broker submit, order boundary를 변경하지 않는다.
- Toss 데이터는 추천/사이클 점수에 직접 반영하지 않는다.
- 실거래 주문 제출은 계속 차단된 상태로 표시한다.
- 기존 route와 visible Korean copy의 의미를 유지한다.

## Scope

- Toss broker data section을 component로 추출한다.
- 컴포넌트는 display-ready props만 받아 렌더링한다.
- 이후 runtime/provider detail extraction으로 이어갈 수 있게 component naming과 test pattern을 유지한다.

## Verification Commands

- verification command: `cd apps/web && npm test -- --run`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13003 npm run test:e2e`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-toss-runtime-section-extraction-v1`
- verification command: `git diff --check`

## Acceptance Criteria

- `/data-health`는 `토스증권 브로커 데이터`, `브로커 현실 데이터`, `증권사 주문 제출 차단`을 계속 렌더링한다.
- 새 component/test 파일은 250 pure LOC를 넘지 않는다.
- `data-health/page.tsx`는 Toss section JSX를 직접 소유하지 않는다.
- E2E와 browser smoke에서 `/data-health` overflow와 raw internal code 노출이 없다.
