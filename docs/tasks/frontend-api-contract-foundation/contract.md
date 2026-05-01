# Task Contract

## Task

- 이름: frontend-api-contract-foundation
- 요청: frontend scaffold 전에 stable read DTO와 example JSON contract를 만든다.
- 담당: Codex
- 날짜: 2026-05-01

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: daily cockpit, remediation tickets, data health, cycle state list, recommendation detail, thesis detail, portfolio coverage에 대한 endpoint contract와 example JSON이 존재하고 검증된다.

## Why

- frontend를 먼저 만들면 DB table/CLI output에 직접 결합된 brittle dashboard가 된다.
- API contract를 먼저 고정해야 Next.js app, Python API adapter, 테스트 fixture를 독립적으로 진행할 수 있다.

## Scope

- 포함:
  - frontend read API contract index
  - seven example response payloads
  - common response convention
  - read/write boundary
  - verification script
  - docs/task handoff 갱신
- 제외:
  - actual API server
  - `apps/web` scaffold
  - UI component implementation
  - auth implementation
  - deployment config
  - DB schema 변경
  - broker/trading integration

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/plans/2026-05-01-frontend-api-contract-foundation.md`
  - `docs/frontend-api-contract.md`
  - `docs/frontend-architecture.md`
  - `docs/api/frontend/`
  - `docs/tasks/frontend-api-contract-foundation/`
  - `docs/verification-plan.md`
  - `scripts/verify_frontend_api_contract.sh`
- 수정 금지 파일:
  - `src/`
  - `tests/`
  - DB migrations
  - deployment secrets
  - package manager files
  - frontend scaffold directories
- 검증에 사용할 명령:
  - `bash -n scripts/verify_frontend_api_contract.sh`
  - `bash scripts/verify_frontend_api_contract.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-contract-foundation`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - frontend API contract doc
  - contract index JSON
  - seven response examples
  - frontend API contract verification script
  - README/verification plan update
  - task contract/plan/handoff/review

## Completion Criteria

- [x] contract index가 endpoint와 example을 연결한다.
- [x] daily cockpit example이 존재한다.
- [x] remediation tickets example이 존재한다.
- [x] data health example이 존재한다.
- [x] cycle state list example이 존재한다.
- [x] recommendation detail example이 존재한다.
- [x] thesis detail example이 존재한다.
- [x] portfolio coverage example이 존재한다.
- [x] actual API server는 생성하지 않는다.
- [x] actual frontend scaffold는 생성하지 않는다.
- [x] docs와 handoff가 갱신된다.
- [x] 하네스 검증이 통과한다.

## Risks

- contract examples는 아직 live DB에서 생성되지 않는다.
- 실제 API adapter 구현 시 DTO field가 일부 조정될 수 있으므로 versioning이 필요하다.
- auth/RBAC는 별도 task가 필요하다.
