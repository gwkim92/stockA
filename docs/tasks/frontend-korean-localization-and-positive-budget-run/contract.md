# Task Contract

## Task

- 이름: frontend-korean-localization-and-positive-budget-run
- 요청: 무료 provider positive-budget 실제 호출 결과를 기록하고, 현재 영어 중심 cockpit 화면을 한국어로 전환한다.
- 담당: Codex
- 날짜: 2026-05-17

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 로컬 Next.js cockpit 주요 화면이 한국어 문구와 한국어 status/action/reason label을 보여주고, `/data-health`가 오늘 무료 provider 호출 한도 소비 상태를 화면에서 확인 가능하게 한다.

## Why

- 현재 local live MVP는 구동되지만 화면 언어가 영어 중심이라 운영자가 투자/데이터 상태를 빠르게 판단하기 어렵다.
- 무료 Alpha Vantage quota는 비용 제약상 운영 리스크이므로 실제 소비 결과와 다음 blocker를 하네스에 남겨야 한다.

## Scope

- Next.js cockpit의 정적 heading, metric label, button, empty/error/loading 문구를 한국어로 바꾼다.
- 화면에 자주 드러나는 backend enum/status/action 값을 한국어 표시 helper로 매핑한다.
- API DTO shape, route 구조, backend SQL, schema, scoring, benchmark, evaluation split은 바꾸지 않는다.
- 무료 provider 실제 호출은 이미 수행된 1회 결과만 기록한다. 같은 날짜에 추가 Alpha Vantage 호출은 명시 승인 전까지 하지 않는다.

## Boundaries

- `.env`와 repo-outside runtime env의 secret 값은 문서나 로그에 남기지 않는다.
- 실제 host scheduler activation, `launchctl bootstrap`, LaunchAgents 쓰기는 하지 않는다.
- 투자 추천 판단 로직은 바꾸지 않는다. 이번 변경은 표시와 운영 가시성에 한정한다.

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/`
  - `apps/web/src/lib/korean-labels.ts`
  - task docs
  - `docs/tasks/local-live-mvp-runtime/handoff.md`
- 수정 금지 파일:
  - `.env`
  - `/private/tmp/stockanalysis-runtime/*.env` secret values
  - `db/migrations/`
  - backend scoring/schema/evaluation logic
  - broker/order flow
  - host scheduler activation files

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `curl -sS -o /private/tmp/stockanalysis-runtime/smoke-home.html -w "%{http_code}\n" http://127.0.0.1:3001/`
  - `curl -sS -o /private/tmp/stockanalysis-runtime/smoke-data-health.html -w "%{http_code}\n" http://127.0.0.1:3001/data-health`
  - `curl -sS -o /private/tmp/stockanalysis-runtime/smoke-remediation.html -w "%{http_code}\n" http://127.0.0.1:3001/remediation`
  - `rg` rendered HTML for targeted old/new text
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task frontend-korean-localization-and-positive-budget-run`
  - `git diff --check`

## Done Criteria

- [x] 주요 cockpit routes의 정적 영어 문구가 한국어로 바뀐다.
- [x] 무료 provider budget card가 positive-budget 시도 후 소비된 호출 수를 표시한다.
- [x] `apps/web` typecheck/build를 수행한다.
- [x] local route smoke로 주요 화면 HTTP 200을 확인한다.
- [x] task handoff에 남은 blocker와 다음 작업을 기록한다.
