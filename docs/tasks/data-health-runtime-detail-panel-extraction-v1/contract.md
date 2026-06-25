# data-health-runtime-detail-panel-extraction-v1 Contract

## Task Request

- request: `/data-health` 대형 페이지에서 provider budget, active recommendation price freshness, open gate freshness, runtime boundary detail panels를 component로 분리한다.
- context: `frontend-domain-component-extraction-v1`에서 상단 overview를 분리했고, `data-health-toss-runtime-section-extraction-v1`에서 Toss 브로커 데이터 섹션을 분리했다. 다음 slice는 하단 운영 상세 패널을 같은 방식으로 추출한다.

## Goal

- goal: 화면 동작과 API DTO를 유지하면서 `/data-health` 하단 세부 패널을 rendering-only operations component로 분리해 `data-health/page.tsx`의 JSX 책임을 줄이고, 이후 남은 운영 상세 섹션도 작은 단위로 이어서 분리할 수 있게 만든다.

## Mutable Surface

- mutable surface:
  - `docs/tasks/data-health-runtime-detail-panel-extraction-v1/*`
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/components/operations/*`

## Invariants

- Backend DTO, DB schema, provider budget policy, data ingest, AI analysis, recommendation scoring, benchmark, portfolio position을 변경하지 않는다.
- broker submit과 실거래 자동화를 열지 않는다.
- `provider-budget`, `active-recommendation-price-freshness`, `runtime-boundary` anchor는 유지한다.
- 새 컴포넌트에는 raw internal code를 직접 노출하지 않고, page에서 만든 한국어 display-ready 값만 넘긴다.

## Scope

- 하단 provider budget, 추천 가격 최신성, open gate freshness, runtime boundary panels를 component로 추출한다.
- 컴포넌트 단위 테스트로 주요 한국어 문구와 내부 코드 미노출을 고정한다.
- 변경은 rendering boundary에 한정한다.

## Verification Commands

- verification command: `cd apps/web && npm test -- --run`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-runtime-detail-panel-extraction-v1`
- verification command: `git diff --check`
- verification command: `Playwright route smoke for http://127.0.0.1:3010/data-health at 375/768/1280px`

## Acceptance Criteria

- `/data-health`는 `데이터 제공자 호출 예산`, `추천에 쓰는 가격이 최신인지 확인`, `조건과 데이터 최신성`, `반복 실행 준비 상태`를 계속 렌더링한다.
- 새 component/test files는 250 pure LOC를 넘지 않는다.
- `/data-health` route smoke에서 가로 overflow가 없고 `broker_submit_allowed`, `read_only_no_order`, `pipeline-run` 같은 raw internal code가 노출되지 않는다.
- 추천 weight, portfolio, benchmark, broker/order boundary가 변경되지 않는다.
