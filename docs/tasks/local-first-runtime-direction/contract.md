# Task Contract

## Task

- 이름: local-first-runtime-direction
- 요청: 외부 서버 배포/서버 scheduler 선택을 즉시 목표에서 내리고, 현재 프로젝트를 local-first 투자 운영 시스템으로 진행한다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - local-first runtime 방향이 문서화된다.
  - "서버"가 화면/API 프로세스와 외부 운영 배포를 혼동하지 않도록 정리된다.
  - server-side scheduler는 미래 옵션으로 남고 immediate next task에서 내려간다.
  - `/data-health`는 외부 server scheduler 배포가 아니라 local runner/operations worker 중심으로 설명한다.
  - 실제 `launchctl`, LaunchAgents write/delete, 외부 배포 작업은 수행하지 않는다.

## Scope

- 포함:
  - `docs/local-first-runtime-direction.md`
  - `docs/server-side-scheduler-architecture.md`
  - `docs/plans/2026-05-20-local-first-runtime-direction.md`
  - `docs/tasks/local-first-runtime-direction/*`
  - `docs/tasks/server-side-scheduler-architecture/handoff.md`
  - `docs/tasks/server-side-scheduler-architecture/review.md`
  - `apps/web/src/app/data-health/page.tsx`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
- 제외:
  - 외부 서버/VPS/GitHub Actions scheduler 배포
  - `launchctl` 실행
  - `~/Library/LaunchAgents` 쓰기/삭제
  - DB schema 변경
  - API/DTO 변경
  - broker/order behavior 변경

## Mutable Surface

- 수정 가능한 파일:
  - `docs/local-first-runtime-direction.md`
  - `docs/server-side-scheduler-architecture.md`
  - `docs/plans/2026-05-20-local-first-runtime-direction.md`
  - `docs/tasks/local-first-runtime-direction/*`
  - `docs/tasks/server-side-scheduler-architecture/handoff.md`
  - `docs/tasks/server-side-scheduler-architecture/review.md`
  - `apps/web/src/app/data-health/page.tsx`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - browser smoke for `/data-health`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task local-first-runtime-direction`
  - `git diff --check`

## Done Criteria

- [x] Local-first runtime direction document exists.
- [x] Roadmap/AGENTS immediate direction is updated.
- [x] Data-health wording no longer makes external server scheduler the immediate target.
- [x] Verification commands pass.
- [x] Handoff and review are updated.
