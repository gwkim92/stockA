# Session Handoff

## Active Task

- 이름: frontend-live-read-event-theme-performance
- 담당: Codex
- 날짜: 2026-05-02

## Current Status

- 완료:
  - event/theme/performance live read slice 구현과 검증을 완료했다.
  - dashboard/data-health live read first slice는 PR #8로 `develop`에 머지됐다.
  - task contract와 plan을 만들었다.
  - `/api/events?asOfDate=...` live read route, SQL renderer, DTO 변환을 추가했다.
  - `/api/themes/:themeKey?asOfDate=...` live read route, SQL renderer, DTO 변환을 추가했다.
  - `/api/performance/:portfolio/outcomes?measurementEndDate=...` live read route, SQL renderer, DTO 변환을 추가했다.
  - 기존 dashboard/data-health/remediation/coverage live read 테스트를 유지하면서 event/theme/performance 테스트를 추가했다.
- 막힌 점:
  - 아직 없음.

## Files Touched

- 생성:
  - `docs/tasks/frontend-live-read-event-theme-performance/contract.md`
  - `docs/tasks/frontend-live-read-event-theme-performance/plan.md`
  - `docs/tasks/frontend-live-read-event-theme-performance/handoff.md`
  - `docs/tasks/frontend-live-read-event-theme-performance/review.md`
- 수정:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/frontend-api-adapter.md`
  - `docs/frontend-api-contract.md`
  - `docs/project-execution-roadmap.md`

## Decisions

- 이 slice는 event/theme/performance live read만 다룬다.
- AI evidence/source document/recommendation/thesis detail live read는 다음 slice로 둔다.
- DB schema와 scoring/benchmark는 건드리지 않는다.
- performance live read는 기존 `performance.recommendation_outcome`, `performance.attribution_run`, `performance.attribution_component`를 읽기만 하며 methodology/scoring을 재계산하지 않는다.

## Verification Already Run

- `python3 -m py_compile src/stockanalysis/frontend/live_adapter.py tests/test_frontend_live_adapter.py`: 통과.
- `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter -v`: 통과, 10 tests.
- `bash scripts/verify_frontend_live_read_adapter.sh`: 통과.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-live-read-event-theme-performance`: 통과.
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 결과 없음.
- `git diff --check`: 통과.
- `PYTHONPATH=src python3 -m unittest discover -s tests`: 통과, 274 tests.

## Still Unverified

- actual external Postgres runtime smoke는 이번 task에서 실행하지 않았다. live SQL은 unit/contract path에서 검증했고, 실제 DB smoke는 별도 runtime/data-ops 단계에서 수행한다.

## Exact Next Step

- exact next step: PR 생성/머지 후 다음 live read slice로 recommendation/thesis detail, AI evidence, source document endpoint를 진행한다.

## Risks

- actual external Postgres runtime smoke는 이 task에서 필수로 두지 않는다. live SQL shape와 adapter contract를 먼저 고정한다.
