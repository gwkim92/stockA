# Session Handoff

## Active Task

- 이름: local-first-runtime-direction
- 담당: Codex
- 날짜: 2026-05-20

## Current Status

- 완료:
  - task contract created.
  - implementation plan created.
  - local-first runtime document, roadmap/AGENTS wording, and `/data-health` copy updates.
  - `docs/server-side-scheduler-architecture.md` reframed as a future external-operation option.
  - `docs/project-execution-roadmap.md` and `AGENTS.md` now make `local-first-runtime-direction` the immediate next task.
  - `/data-health` now explains local manual/local runner execution through `stockanalysis-operations` worker.
- 막힌 점:
  - none currently.

## Exact Next Step

- 다음 세션은 이것부터 시작: local one-command run/status orchestration을 만든다. 우선 local runtime status, local operations worker command matrix, 수동 ingest smoke, `/data-health` 반영 순서로 진행한다.
- 금지: 명시 승인 전까지 `launchctl bootstrap/kickstart`, `~/Library/LaunchAgents` write/delete, 외부 server scheduler 배포는 하지 않는다.

## Verification

- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- Browser smoke: `http://127.0.0.1:3001/data-health`, title `데이터 수집 | 스톡애널리시스 대시보드`, local-first wording checks true, console error count 0.
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task local-first-runtime-direction`
- `git diff --check`

## Risks

- 이 작업은 architecture direction and UI wording change다. 실제 scheduler 배포나 host mutation은 하지 않는다.
- 아직 local one-command run/status orchestration은 구현되지 않았다. 다음 작업에서 로컬 실행 상태 점검과 수동 ingest smoke를 제품 경계로 묶어야 한다.
