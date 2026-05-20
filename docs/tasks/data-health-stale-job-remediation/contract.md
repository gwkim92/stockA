# Task Contract

## Task

- 이름: data-health-stale-job-remediation
- 요청: `/data-health`에 남아 있는 stale/missing 운영 작업을 scheduler 없이 수동 단발 실행으로 줄인다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: local live MVP의 `/api/data-health`에서 stale daily portfolio jobs는 최신 수동 실행 결과를 반영하고, monthly performance missing 상태는 실행 성공 또는 구체적 차단 원인으로 설명된다.

## Why

- 현재 frontend/backend는 live DB를 읽고 있지만, operator 관점에서는 stale/missing 상태가 남아 있어 실제 구동 MVP 신뢰도가 낮다.
- recurring scheduler activation은 아직 명시 승인 전까지 금지되어 있으므로, 먼저 `stockanalysis-operations run` 경계로 단발 실행과 artifact provenance를 증명해야 한다.

## Scope

- 현재 live `/api/data-health`의 stale/missing problem runs를 확인한다.
- `portfolio-position-daily`와 `portfolio-remediation-daily`를 repo-outside runtime env와 artifact runner 경계로 실행한다.
- `performance-outcome-monthly`는 실행 가능한지 확인하고, 실패하면 stdout/stderr/metadata artifact와 root cause를 남긴다.
- 실행 후 `/api/data-health`를 다시 조회해 상태 변화를 기록한다.
- task handoff/review와 local live MVP handoff를 갱신한다.

## Boundaries

- 실제 `launchctl bootstrap`, `kickstart`, `~/Library/LaunchAgents` 쓰기는 하지 않는다.
- `.env` 또는 provider API key 값을 출력하거나 repo에 저장하지 않는다.
- DB schema, scoring, benchmark, evaluation split, broker/order flow는 바꾸지 않는다.
- product orchestration을 새 shell script로 늘리지 않고 기존 `stockanalysis-operations` backend CLI/service boundary를 우선 사용한다.

## Mutable Surface

- 수정 가능한 파일:
  - `docs/tasks/data-health-stale-job-remediation/*`
  - `docs/tasks/local-live-mvp-runtime/handoff.md`
  - 필요 시 `docs/tasks/local-live-mvp-runtime/review.md`
- repo-outside runtime artifact:
  - `/private/tmp/stockanalysis-runtime/artifacts/*`

## Verification Commands

- 검증에 사용할 명령:
  - authorized `/api/data-health` live query before/after
  - `stockanalysis-operations run` artifacts for affected jobs
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task data-health-stale-job-remediation`
  - `git diff --check`

## Done Criteria

- [x] before/after `/api/data-health` evidence가 기록된다.
- [x] stale daily portfolio jobs가 수동 단발 실행 결과로 갱신된다.
- [x] monthly performance missing 상태가 성공 또는 차단 원인으로 설명된다.
- [x] task handoff/review가 다음 사람이 이어받을 수 있게 갱신된다.
