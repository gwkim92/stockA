# data-health-command-center-v2 Contract

## Task Request

- request: `/data-health`가 운영자 로그처럼 보이고, 사용자가 지금 무엇을 먼저 봐야 하는지 이해하기 어렵다. 전체 상태를 장애, 관리 대기, 원천 한계, 자동 수집, AI 품질, 투자 안전 경계로 나눠 첫 화면에서 판단 가능하게 만든다.

## Goal

- goal: `/data-health` 상단이 `오늘 먼저 볼 것`을 명확히 제시하고, 세부 로그를 보기 전에 `즉시 조치`, `자동 수집`, `데이터·AI 품질`, `투자 안전`, `원천 한계` 상태를 한국어로 분리해서 보여준다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/data-health-command-center-v2/*`

## Scope

- Add a command-center style summary section near the top of `/data-health`.
- Reduce duplicate priority cards on the first screen.
- Keep detailed execution tables and existing sections available below.
- Keep all API contracts, scheduler behavior, recommendation scoring, portfolio state, schema, and broker/order boundaries unchanged.

## Non-Goals

- Do not change backend data-health payload generation.
- Do not change scheduler cadence or systemd units.
- Do not change recommendation weights, benchmark definitions, portfolio positions, or trading boundaries.
- Do not add paid observability, RAG, graph, or alerting services.

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-command-center-v2`
- verification command: EC2 route smoke for `/data-health` and `/api/data-health`.
- verification command: Browser smoke through `http://127.0.0.1:13000/data-health`.

## Acceptance Criteria

- `/data-health` top area states what to inspect first.
- The page separates true blockers from managed waits and source limitations.
- Scheduler/collection status is grouped by user meaning, not raw job names only.
- User-facing copy avoids raw internal terms where practical.
- No scoring, portfolio, benchmark, schema, scheduler, or order mutation is introduced.
