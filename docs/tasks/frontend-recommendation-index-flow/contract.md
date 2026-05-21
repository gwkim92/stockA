# Task Contract

## Task

- 이름: frontend-recommendation-index-flow
- 요청: `/recommendations`에서 최신 추천 목록을 보고 상세/종목/투자 논리/AI 근거로 이동할 수 있게 한다.
- 담당: Codex
- 날짜: 2026-05-21

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `GET /api/recommendations` read-only DTO와 Next.js `/recommendations` 화면이 존재하고, 사용자가 최신 추천 배치의 종목, 점수, 근거 품질, 투자 논리, 성과 상태를 확인한 뒤 상세/종목/보유검토/AI 근거 화면으로 이동할 수 있다.

## Why

- 기존 nav의 추천 링크는 특정 상세 URL로 바로 이동해서 추천 목록과 현재 배치 상태를 볼 수 없었다.
- 사용자는 신호/추천/보유검토가 어디에 있는지 혼란스러워했고, 추천 흐름의 중간 관제 화면이 필요하다.
- 추천은 주문이 아니라 검토 입력값이므로 목록에서 근거 연결 상태와 차단/보강 상태를 먼저 보여줘야 한다.

## Scope

- 포함:
  - read-only `/api/recommendations` frontend API contract and fixture
  - live Postgres adapter support for `/api/recommendations`
  - pagination registration for recommendation list
  - Next.js `/recommendations` page
  - nav update from hardcoded recommendation detail to index
  - focused tests and task docs
- 제외:
  - recommendation scoring formula change
  - DB migration or schema change
  - broker/order flow
  - write APIs
  - real trading activation

## Mutable Surface

- 수정 가능한 파일:
  - `docs/api/frontend/contract-index.json`
  - `docs/api/frontend/examples/recommendation-list.json`
  - `docs/frontend-api-contract.md`
  - `docs/frontend-api-adapter.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `scripts/verify_frontend_api_contract.sh`
  - `scripts/verify_frontend_api_adapter.sh`
  - `scripts/verify_frontend_fixture_server.sh`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `src/stockanalysis/frontend/pagination.py`
  - `apps/web/src/app/recommendations/page.tsx`
  - `apps/web/src/app/layout.tsx`
  - `apps/web/src/lib/frontend-api.ts`
  - `apps/web/src/lib/types.ts`
  - focused tests
  - `docs/tasks/frontend-recommendation-index-flow/`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations
  - scoring formula
  - benchmark/evaluation split
  - broker/order submission code
  - production secret/deployment credentials

## Verification

- 검증에 사용할 명령:
  - `bash scripts/verify_frontend_api_contract.sh`
  - `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter tests.test_frontend_api_adapter tests.test_frontend_fixture_server -v`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest tests.test_frontend_api_server -v`
  - `bash scripts/verify_frontend_api_adapter.sh`
  - `bash scripts/verify_frontend_fixture_server.sh`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task frontend-recommendation-index-flow`

## Done Criteria

- [x] `/api/recommendations` appears in frontend contract index.
- [x] Fixture payload resolves for `/api/recommendations`.
- [x] Live adapter returns a bounded read-only recommendation list from canonical Postgres tables.
- [x] `/recommendations` page renders and links to recommendation detail, stock detail, thesis, AI evidence, paper trading, and portfolio coverage.
- [x] Focused verification commands pass.
