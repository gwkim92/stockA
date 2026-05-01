# Task Contract

## Task

- 이름: frontend-ai-evidence-route
- 요청: AI evidence와 source document를 검토하는 read-only frontend route를 추가한다.
- 담당: Codex
- 날짜: 2026-05-01

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `apps/web`에서 `/ai-evidence/sec-event-aapl-10k-20240928`와 `/source-documents/aapl-2024-10k-20240928`가 fixture payload를 읽고, AI 추출 결과와 원문 출처/provenance를 연결해 보여준다.

## Scope

- 포함:
  - frontend API contract에 AI evidence/source document DTO 추가
  - fixture examples 추가
  - frontend API client/types 확장
  - read-only Next.js App Router pages 추가
  - recommendation/thesis detail에서 evidence drilldown link 연결
  - verification scripts/tests/docs 갱신
- 제외:
  - live DB read adapter
  - browser-side LLM call
  - prompt 실행 또는 재생성 mutation
  - raw document download/auth/RBAC
  - 투자 추천 로직 변경

## Mutable Surface

- 수정 가능한 파일:
  - `docs/api/frontend/`
  - `docs/frontend-api-contract.md`
  - `docs/frontend-architecture.md`
  - `docs/apps-web-scaffold.md`
  - `docs/verification-plan.md`
  - `docs/tasks/frontend-ai-evidence-route/`
  - `apps/web/src/app/`
  - `apps/web/src/lib/`
  - `scripts/verify_frontend_api_contract.sh`
  - `scripts/verify_frontend_detail_routes.sh`
  - `tests/test_frontend_api_adapter.py`
  - `tests/test_frontend_fixture_server.py`
- 수정 금지 파일:
  - DB migrations
  - secrets
  - live trading integrations
  - scoring/evaluation benchmark

- 검증에 사용할 명령:
  - `bash scripts/verify_frontend_detail_routes.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-ai-evidence-route`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`
  - Playwright smoke for `/ai-evidence/sec-event-aapl-10k-20240928` and `/source-documents/aapl-2024-10k-20240928`

## Completion Criteria

- [x] AI evidence API fixture is registered in `contract-index.json`.
- [x] Source document API fixture is registered in `contract-index.json`.
- [x] AI evidence route renders extraction fields, source chunks, provenance, and token/cost metadata.
- [x] Source document route renders source metadata, storage/provenance, and linked AI evidence.
- [x] Recommendation/thesis detail routes link to evidence drilldown without making non-source evidence look clickable.
- [x] verification script covers the new routes.
- [x] AWH readiness checks pass.

## Risks

- Current payload is fixture-only and does not prove live source freshness.
- The first route supports one known SEC event/source document pair.
- Browser route is read-only; any regeneration or review-note write flow remains out of scope.
