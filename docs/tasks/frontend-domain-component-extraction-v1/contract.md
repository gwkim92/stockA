# frontend-domain-component-extraction-v1 Contract

## Task Request

- request: 전문 투자 리서치 워크스페이스 재설계 이후 남은 대형 프론트엔드 파일을 작게 나누어 유지보수성과 검증 가능성을 높인다.
- context: 이전 UI 개편은 EC2 배포까지 완료됐지만, `data-health`, 종목 상세, 추천 상세, AI 근거 상세 같은 페이지가 여전히 과도하게 크다. 첫 slice는 가장 큰 운영 콘솔인 `data-health`에서 시작한다.

## Goal

- goal: 화면 동작과 API DTO를 유지하면서 `data-health` 페이지의 반복 섹션을 도메인 컴포넌트로 분리하고, 이후 종목·추천·AI 근거 상세를 같은 방식으로 이어갈 수 있는 구조를 만든다.

## Mutable Surface

- mutable surface:
  - `docs/tasks/frontend-domain-component-extraction-v1/*`
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/components/operations/*`
  - `apps/web/src/lib/presentation/*`
  - 관련 frontend test files

## Invariants

- FastAPI/backend DTO, DB schema, ingest, AI extraction, validator, cycle calculation, recommendation score/weight, benchmark, portfolio position을 변경하지 않는다.
- broker submit과 실거래 자동화를 열지 않는다.
- 기존 public route와 frontend API DTO를 유지한다.
- 사용자에게 보이는 주요 문구 의미를 바꾸지 않는다. 문구 변경이 필요하면 운영자 용어 제거 수준으로만 제한한다.
- EC2는 `develop`만 pull한다. feature branch 검증 후 `develop`에 반영한다.

## Scope

- `data-health`에서 동일 책임을 가진 섹션을 추출한다.
- 추출 컴포넌트는 page-level data를 props로 받아 렌더링만 담당한다.
- 기존 E2E가 보는 핵심 문구와 route behavior를 유지한다.
- 첫 작업에서 backend, scheduler, AI provider, recommendation scoring은 건드리지 않는다.

## Verification Commands

- verification command: `cd apps/web && npm test -- --run`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13003 npm run test:e2e`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task frontend-domain-component-extraction-v1`
- verification command: `git diff --check`

## Acceptance Criteria

- `data-health` route가 기존 주요 운영 카드를 계속 렌더링한다.
- 투자 판단 화면에는 내부 운영 용어가 새로 노출되지 않는다.
- 추출된 컴포넌트는 단일 책임을 갖고, 새 파일은 250 pure LOC를 넘지 않는다.
- TypeScript typecheck와 Next build가 통과한다.
- E2E smoke에서 `/data-health` desktop/tablet/mobile 가로 넘침과 내부 코드 노출 검사가 계속 통과한다.
