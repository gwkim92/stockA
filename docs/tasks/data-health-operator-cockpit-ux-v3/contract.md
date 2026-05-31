# data-health-operator-cockpit-ux-v3

## Task Request

- request: `/data-health` 운영 상태 화면을 개발자 로그가 아니라 사용자가 수집·분석·추천 준비 상태를 이해하는 관제 화면으로 정리한다.

## Goal

- goal: 데이터 수집, 뉴스 AI 분석, 품질 감사, 추천/성과 대기, 알림/권한 상태를 `정상`, `확인 필요`, `대기 중`, `차단 중`으로 구분해 보여준다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/data-health/page.tsx`
  - `docs/tasks/data-health-operator-cockpit-ux-v3/*`

## Non-Goals

- DB/API DTO, scheduler cadence, AI batch, alert destination, auth/RBAC, recommendation scoring, broker/order flow는 변경하지 않는다.
- 운영 상태 값을 숨기거나 성공처럼 포장하지 않는다. 단, 내부 ID와 raw code는 사용자용 설명으로 바꾼다.

## Acceptance Criteria

- 첫 화면에서 `수집`, `AI 분석`, `추천/성과`, `운영 안전`, `확인 필요`가 바로 보인다.
- `pipeline-run`, `eval_run_id`, `attention_required`, `open_gate`, raw status code 같은 내부 표현이 주요 사용자 문구로 노출되지 않는다.
- 실패·대기·원천 한계·성과 성숙 대기·주문 차단이 사용자용 한국어로 명확히 보인다.
- Next.js typecheck/build, AWH verify, diff check를 통과한다.
- EC2 route/content smoke와 Playwright snapshot으로 핵심 문구를 확인한다.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-operator-cockpit-ux-v3`
- verification command: `git diff --check`
- verification command: EC2 route/content smoke for `/data-health`
- verification command: Playwright snapshot for `http://127.0.0.1:13000/data-health`

## Boundaries

- 이번 작업은 UX/copy visibility slice다.
- 실제 운영 스케줄, 데이터 수집, AI 호출, 추천 산식, 거래 경계는 바꾸지 않는다.
