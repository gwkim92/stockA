# Session Handoff

## Active Task

- 이름: server-side-scheduler-architecture
- 담당: Codex
- 날짜: 2026-05-20

## Current Status

- 완료:
  - task contract created.
  - implementation plan created.
  - server-side scheduler architecture document drafted.
  - UI and roadmap wording updates.
  - `/data-health` now explains that the operating target is a server-side scheduler plus `stockanalysis-operations` worker, not Mac LaunchAgents.
  - `AGENTS.md` and `docs/project-execution-roadmap.md` now demote Mac LaunchAgents to local MVP/operator-only and make server scheduler architecture the immediate next direction.
- 진행 중:
  - none.
- 막힌 점:
  - none currently.

## Exact Next Step

- 후속 결정으로 immediate next는 `local-first-runtime-direction`으로 변경됐다.
- 다음 세션은 이것부터 시작: 외부 server scheduler target 선택이 아니라 local runtime status, local operations worker command matrix, 수동 ingest smoke, `/data-health` 반영을 먼저 진행한다.
- 금지: 명시 승인 전까지 `launchctl bootstrap/kickstart`, `~/Library/LaunchAgents` write/delete, host scheduler 실제 설치는 하지 않는다.

## Verification

- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- Browser smoke: `http://127.0.0.1:3001/data-health` shows "운영 스케줄러는 아직 배포되지 않음" and "웹 서버가 아니라 서버 scheduler가 worker를 실행한다"; browser console error count 0.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task server-side-scheduler-architecture`
- `git diff --check`

## Risks

- 이 작업은 architecture direction and UI wording change다. 실제 scheduler 배포나 host mutation은 하지 않는다.
- 아직 external server scheduler provider, deployment manifest, retry/alert runtime은 구현되지 않았다. 단, 이 범위는 future option으로 내려갔고 immediate work는 local-first runtime 안정화다.
