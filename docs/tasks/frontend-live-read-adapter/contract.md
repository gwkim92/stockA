# Task Contract

## Task

- 이름: frontend-live-read-adapter
- 요청: fixture-only frontend API adapter 뒤에 live Postgres read adapter pilot을 추가한다.
- 담당: Codex
- 날짜: 2026-05-01

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: frontend contract DTO를 유지하면서 일부 read endpoint가 canonical Postgres report를 live source로 읽을 수 있고, DB가 없을 때 fixture fallback을 유지한다.

## Why

- 프론트가 계속 fixture JSON만 읽으면 실제 데이터 수집기와 운영 DB의 freshness를 검증할 수 없다.
- 단번에 production API server를 만들기보다 read adapter boundary를 먼저 만들면 계약, 테스트, fallback을 유지하면서 live 데이터로 확장할 수 있다.

## Scope

- 포함:
  - live read adapter module
  - `GET /api/remediation-tickets?status=open` live DTO 변환
  - `GET /api/portfolio/:portfolioName/coverage?asOfDate=...` live DTO 변환
  - CLI `get --source fixture|live|auto`
  - tests
  - verification script
  - docs/task handoff 갱신
- 제외:
  - production HTTP API server
  - auth/RBAC
  - write endpoint
  - DB schema/benchmark/evaluation 기준 변경
  - frontend route redesign
  - broker/order integration

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/`
  - `src/stockanalysis/performance/coverage.py`
  - `src/stockanalysis/signal/portfolio_remediation_ticket.py`
  - `tests/test_frontend_api_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `scripts/verify_frontend_live_read_adapter.sh`
  - `docs/frontend-api-adapter.md`
  - `docs/frontend-api-contract.md`
  - `docs/frontend-architecture.md`
  - `docs/verification-plan.md`
  - `docs/tasks/frontend-live-read-adapter/`
- 수정 금지 파일:
  - DB migrations
  - secrets/env files
  - benchmark math
  - trading or broker integration
- 검증에 사용할 명령:
  - `bash -n scripts/verify_frontend_live_read_adapter.sh`
  - `bash scripts/verify_frontend_live_read_adapter.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-live-read-adapter`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - live read adapter module
  - live adapter tests
  - CLI source mode
  - verification script
  - updated docs
  - task contract/plan/handoff/review

## Completion Criteria

- [x] live remediation ticket response가 frontend contract shape로 반환된다.
- [x] live portfolio coverage response가 frontend contract shape로 반환된다.
- [x] `--source live`는 DB config가 없으면 stable error를 반환한다.
- [x] `--source auto`는 DB config가 없으면 fixture로 안전하게 fallback한다.
- [x] fixture adapter 기존 동작이 깨지지 않는다.
- [x] docs와 handoff가 갱신된다.
- [x] 하네스 검증이 통과한다.

## Risks

- live pilot은 모든 12개 endpoint를 지원하지 않는다.
- live DTO id는 frontend용 opaque id로 변환되므로 아직 detail route live lookup과 1:1 연결되지 않을 수 있다.
- `psql` command 기반이므로 production API latency/connection pooling은 별도 단계에서 다뤄야 한다.
