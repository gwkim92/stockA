# data-health-control-room-ux-v2 Contract

## Task Request

- request: `/data-health` 화면을 운영자 로그 나열이 아니라 사용자가 바로 판단할 수 있는 수집·자동화·품질·투자 경계 판정판으로 재구성한다.

## Goal

- goal: `/data-health` 첫 화면에서 현재 서비스가 정상인지, 자동 수집이 돌고 있는지, 데이터/AI 품질에 문제가 있는지, 추천 weight·주문이 차단되어 있는지 한눈에 알 수 있다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/data-health-control-room-ux-v2/*`

## Invariants

- recommendation weight, scoring formula, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- DB schema, FastAPI contract, scheduler, data ingest, AI batch runtime은 변경하지 않는다.
- 화면은 저장된 read-only 운영 상태만 조합하며 쓰기/재실행/주문 버튼을 추가하지 않는다.

## Scope

- 중복되는 상단 판단 strip을 제거한다.
- `/data-health` 상단에 `운영 판정판`을 추가한다.
- 판정 축은 `서비스 접근`, `자동 수집`, `데이터·AI 품질`, `투자 경계`로 고정한다.
- 기존 실행 이력, 품질 감사, AI 회귀평가, 전문 분석 상세는 아래 세부 섹션으로 유지한다.
- 모바일에서 판정 카드가 1열로 내려오도록 CSS를 추가한다.

## Non-Goals

- 실제 scheduler 실행 주기 변경 금지
- 알림 목적지 변경 금지
- API 권한 정책 변경 금지
- 추천/거래 로직 변경 금지

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-control-room-ux-v2`
- verification command: `git diff --check`
- verification command: EC2 또는 local tunnel에서 `/data-health` route smoke

## Done Criteria

- [x] `/data-health` 상단에 `운영 판정판`이 렌더링된다.
- [x] `서비스 접근`, `자동 수집`, `데이터·AI 품질`, `투자 경계`가 첫 화면에 보인다.
- [x] 기존 실행 이력과 세부 품질 정보는 아래 섹션으로 유지된다.
- [x] local verification과 EC2 route smoke가 통과한다.
