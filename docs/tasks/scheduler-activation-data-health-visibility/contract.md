# Task Contract

## Task

- 이름: scheduler-activation-data-health-visibility
- 요청: `/api/data-health`와 `/data-health`에서 scheduler activation approval 상태를 안전하게 보여준다.
- 담당: Codex
- 날짜: 2026-05-18

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: repo-outside approval gate report가 설정되면 data-health DTO와 화면이 `market-price-daily` scheduler가 준비됐지만 manual approval pending 상태임을 secret/path 없이 보여준다.

## Why

- local MVP는 `market-price-daily` operator dry-run과 pending approval gate evidence를 만들었다.
- 하지만 화면은 아직 scheduler 상태를 `not_installed` 정도로만 보여주므로, 사용자가 “실제 자동화가 어디서 막혔는지” 판단하기 어렵다.

## Scope

- data-health live adapter에 scheduler approval gate report sanitizer를 추가한다.
- report path는 repo-outside env로 주입하고, 응답에는 경로/secret을 노출하지 않는다.
- Next `/data-health` 화면에 scheduler activation 상태 카드를 추가한다.
- contract example, TypeScript type, focused tests, task handoff/review를 갱신한다.

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/korean-labels.ts`
  - `docs/api/frontend/examples/data-health.json`
  - task docs
  - repo-outside `/private/tmp/stockanalysis-runtime/frontend-api.env`
- 수정 금지 파일:
  - repo-inside `.env` secret values
  - DB migrations
  - scoring/benchmark/evaluation split
  - broker/order flow
  - host LaunchAgents path

## Boundaries

- 실제 `launchctl` 실행, LaunchAgents 쓰기, scheduler activation은 하지 않는다.
- approval gate report의 raw path, env values, provider keys, DB URL은 API/화면에 노출하지 않는다.
- DTO 변경은 additive로 제한한다.

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - browser smoke for `http://127.0.0.1:3001/data-health`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task scheduler-activation-data-health-visibility`
  - `git diff --check`

## Done Criteria

- [x] data-health DTO includes sanitized scheduler activation state.
- [x] `/data-health` renders scheduler approval status in Korean.
- [x] missing/invalid report paths degrade safely.
- [x] verification evidence is recorded in handoff/review.
