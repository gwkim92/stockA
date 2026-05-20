# Task Contract

## Task

- 이름: frontend-live-evidence-linking
- 요청: live DB 기반 화면에서 이벤트, 원천 문서, AI 증거가 실제 연결 관계대로 보이도록 고친다.
- 담당: Codex
- 날짜: 2026-05-18

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: FastAPI live adapter가 `ai.extraction_artifact.event_id`가 비어 있고 `document_id`만 있는 실제 추출 artifact도 이벤트/테마/문서/증거 상세 화면에 연결한다.

## Why

- 로컬 live DB에는 SEC 문서 기반 AI 추출 artifact가 `document_id`로 저장되어 있다.
- 기존 화면 경계는 대부분 `artifact.event_id = event.event_id`만 확인해서 이벤트 목록과 테마 상세에서 증거 링크가 빠지고, `source-document-<external_id>` 식별자도 제대로 해석하지 못했다.

## Scope

- frontend live SQL의 evidence lookup 조건을 document-linked artifact까지 확장한다.
- source document detail과 AI evidence detail route가 `source-document-<external_document_id>`, `ai-evidence-<id>`, `event-<id>`를 안정적으로 처리하게 한다.
- 깨진 정적 내비게이션 증거 링크를 실제 live DB 식별자 형식으로 바꾼다.
- 회귀 테스트는 SQL 문자열과 기존 DTO contract shape 중심으로 추가한다.

## Boundaries

- DB schema, seed, scoring, benchmark, evaluation split은 바꾸지 않는다.
- AI 추출 품질 자체를 개선하지 않는다. 이번 범위는 이미 저장된 artifact를 화면에 정확히 연결하는 것이다.
- 새로운 write API, broker/order flow, scheduler activation은 범위 밖이다.

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/app/layout.tsx`
  - `tests/test_frontend_live_adapter.py`
  - task docs

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`

## Done Criteria

- [x] event/theme SQL이 document-linked extraction artifact를 evidence로 잡는다.
- [x] source document detail SQL이 `source-document-<external_document_id>`를 해석한다.
- [x] AI evidence detail SQL이 source-document-prefixed external id와 event opaque id를 해석한다.
- [x] `/ai-evidence/...` 정적 내비게이션이 live DB에서 해석 가능한 링크를 쓴다.
- [x] focused backend/frontend 검증이 통과한다.
