# Task Contract

## Task

- 이름: server-side-scheduler-architecture
- 요청: MacBook LaunchAgents가 아니라 서버형 scheduler/worker 구조를 최종 방향으로 고정한다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 서버형 scheduler + worker 구조가 문서화된다.
  - Mac LaunchAgents는 local MVP/개발 옵션이고 최종 운영 경로가 아니라는 점이 명확하다.
  - `/data-health` 화면 문구가 “Mac host scheduler” 중심에서 “운영 scheduler 미배포” 중심으로 정리된다.
  - 실제 `launchctl`, LaunchAgents write/delete, scheduler 배포는 수행하지 않는다.

## Scope

- 포함:
  - `docs/server-side-scheduler-architecture.md`
  - `docs/plans/2026-05-20-server-side-scheduler-architecture.md`
  - `docs/tasks/server-side-scheduler-architecture/*`
  - `apps/web/src/app/data-health/page.tsx`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
- 제외:
  - 실제 scheduler 배포
  - `launchctl` 실행
  - `~/Library/LaunchAgents` 쓰기/삭제
  - DB schema 변경
  - API/DTO 변경
  - trading/order behavior 변경

## Mutable Surface

- 수정 가능한 파일:
  - `docs/server-side-scheduler-architecture.md`
  - `docs/plans/2026-05-20-server-side-scheduler-architecture.md`
  - `docs/tasks/server-side-scheduler-architecture/*`
  - `apps/web/src/app/data-health/page.tsx`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - browser smoke for `/data-health`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task server-side-scheduler-architecture`
  - `git diff --check`

## Done Criteria

- [x] Server-side scheduler architecture document exists.
- [x] Data-health wording separates current local evidence from target server scheduler.
- [x] Roadmap/AGENTS next direction is updated.
- [x] Verification commands pass.
- [x] Handoff and review are updated.
