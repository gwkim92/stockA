# Task Contract

## Task

- 이름: scheduler-activation-readiness-dashboard
- 요청: scheduler 실제 활성화가 왜 아직 안 되는지 `/data-health`에서 사람이 바로 판단할 수 있게 만든다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/data-health`가 scheduler activation 결론, 승인 관문, activation 가능 여부, 다음 조치, 증거 위치를 한 카드에서 보여준다.
  - 화면은 “최근 실행 성공”과 “반복 실행 미설치/승인 대기”를 명확히 분리한다.
  - host scheduler activation, launchctl, LaunchAgents write, env/secrets, DB schema, backend DTO는 변경하지 않는다.

## Scope

- 포함:
  - `apps/web/src/app/data-health/page.tsx`
  - docs plan/task
- 제외:
  - backend API/DTO changes
  - DB migration
  - real scheduler activation
  - launchd plist install/write/delete
  - env/secrets changes
  - paper/live order writes

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/data-health/page.tsx`
  - `docs/plans/2026-05-20-scheduler-activation-readiness-dashboard.md`
  - `docs/tasks/scheduler-activation-readiness-dashboard/*`

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - browser smoke for `/data-health`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task scheduler-activation-readiness-dashboard`
  - `git diff --check`

## Done Criteria

- [x] Scheduler activation readiness card is visible on `/data-health`.
- [x] Card explains why actual repeat automation is not active.
- [x] Browser smoke confirms the section is visible.
- [x] Verification commands pass.
- [x] Handoff and review are updated.
