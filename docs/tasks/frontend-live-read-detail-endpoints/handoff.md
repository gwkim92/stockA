# Session Handoff

## Active Task

- 이름: frontend-live-read-detail-endpoints
- 담당: Codex
- 날짜: 2026-05-02

## Current Status

- 완료:
  - detail endpoint live read slice 구현과 검증을 완료했다.
  - dashboard/data-health는 PR #8로 `develop`에 머지됐다.
  - event/theme/performance는 PR #9로 `develop`에 머지됐다.
  - task contract와 plan을 만들었다.
  - `/api/recommendations/:id` live read route, SQL renderer, DTO 변환을 추가했다.
  - `/api/theses/:id` live read route, SQL renderer, DTO 변환을 추가했다.
  - `/api/ai-evidence/:id` live read route, SQL renderer, DTO 변환을 추가했다.
  - `/api/source-documents/:id` live read route, SQL renderer, DTO 변환을 추가했다.
  - schema self-review에서 thesis outcome 컬럼명과 AI artifact document-link fallback을 보강했다.
- 막힌 점:
  - 아직 없음.

## Files Touched

- 생성:
  - `docs/plans/2026-05-02-frontend-live-read-detail-endpoints.md`
  - `docs/tasks/frontend-live-read-detail-endpoints/contract.md`
  - `docs/tasks/frontend-live-read-detail-endpoints/plan.md`
  - `docs/tasks/frontend-live-read-detail-endpoints/handoff.md`
  - `docs/tasks/frontend-live-read-detail-endpoints/review.md`
- 수정:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/frontend-api-adapter.md`
  - `docs/frontend-api-contract.md`
  - `docs/project-execution-roadmap.md`

## Decisions

- 이 slice는 recommendation/thesis/AI evidence/source document detail live read만 다룬다.
- DB schema와 scoring/benchmark는 건드리지 않는다.
- source document raw download은 auth/RBAC 전까지 계속 비활성화한다.
- path ID는 fixture slug와 opaque numeric prefix를 모두 보수적으로 지원한다.

## Verification Already Run

- `python3 -m py_compile src/stockanalysis/frontend/live_adapter.py tests/test_frontend_live_adapter.py`: 통과.
- `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter -v`: 통과, 15 tests.
- `bash scripts/verify_frontend_live_read_adapter.sh`: 통과.
- `bash scripts/verify_project_execution_roadmap.sh`: 통과.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-live-read-detail-endpoints`: 통과.
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 결과 없음.
- `git diff --check`: 통과.
- `PYTHONPATH=src python3 -m unittest discover -s tests`: 통과, 279 tests.

## Still Unverified

- actual external Postgres runtime smoke는 이번 task에서 실행하지 않았다. live SQL은 unit/contract path에서 검증했고, 실제 DB smoke는 별도 runtime/data-ops 단계에서 수행한다.

## Exact Next Step

- exact next step: PR 생성/머지 후 마지막 live read gap인 `/api/cycles?asOfDate=...`를 진행하거나 production API runtime boundary로 넘어가기 전 cycle list를 완료한다.

## Risks

- actual external Postgres runtime smoke는 이 task에서 필수로 두지 않는다. live SQL shape와 adapter contract를 먼저 고정한다.
