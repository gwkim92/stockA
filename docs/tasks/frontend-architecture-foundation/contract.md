# Task Contract

## Task

- 이름: frontend-architecture-foundation
- 요청: 현재 프로젝트에 프론트엔드가 없는 상태를 점검하고, 어떤 프론트를 어떻게 구성할지 설계해 보고한다.
- 담당: Codex
- 날짜: 2026-05-01

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: frontend의 목적, route map, API boundary, AI boundary, security boundary, implementation phases가 문서화되어 다음 세션에서 scaffold 또는 API contract 작업을 바로 시작할 수 있다.

## Why

- 현재 구현은 ingest, cycle, thesis, remediation, scheduler 중심이며 사람이 매일 판단할 운영 화면이 없다.
- 프론트를 성급히 만들면 DB schema와 CLI에 직접 결합된 brittle dashboard가 되므로, 먼저 운영 cockpit의 역할과 데이터 경계를 고정해야 한다.

## Scope

- 포함:
  - frontend architecture doc
  - route IA
  - API/backend boundary
  - AI role in frontend
  - staged implementation plan
  - verification script
  - docs/task handoff 갱신
- 제외:
  - actual `apps/web` scaffold
  - UI component implementation
  - API endpoint implementation
  - auth implementation
  - deployment config
  - broker/trading integration

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/plans/2026-05-01-frontend-architecture-foundation.md`
  - `docs/frontend-architecture.md`
  - `docs/tasks/frontend-architecture-foundation/`
  - `docs/verification-plan.md`
  - `scripts/verify_frontend_architecture.sh`
- 수정 금지 파일:
  - `src/`
  - `tests/`
  - DB migrations
  - deployment secrets
  - package manager files
  - frontend scaffold directories
- 검증에 사용할 명령:
  - `bash -n scripts/verify_frontend_architecture.sh`
  - `bash scripts/verify_frontend_architecture.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-architecture-foundation`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - frontend architecture doc
  - frontend architecture verification script
  - README/verification plan update
  - task contract/plan/handoff/review

## Completion Criteria

- [x] 현재 frontend가 없다는 상태가 문서화된다.
- [x] frontend 목적이 investment cockpit으로 정의된다.
- [x] route map이 정의된다.
- [x] API/backend boundary가 정의된다.
- [x] AI role과 token/cost boundary가 정의된다.
- [x] security/read-only-first boundary가 정의된다.
- [x] actual scaffold는 생성하지 않는다.
- [x] docs와 handoff가 갱신된다.
- [x] 하네스 검증이 통과한다.

## Risks

- frontend scaffold 없이 문서만 있으므로 아직 사용자 화면은 없다.
- 최신 frontend stack은 실제 scaffold 시점에 다시 version pinning이 필요하다.
- API contract가 없으면 frontend 구현이 DB schema에 과결합될 수 있다.
