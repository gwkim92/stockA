# Session Handoff

## Active Task

- 이름: frontend-live-evidence-linking
- 담당: Codex
- 날짜: 2026-05-18

## Current Status

- 완료:
  - root cause confirmed: real local DB has `ai.extraction_artifact.document_id` populated while `event_id` is null.
  - impacted surfaces identified: event list, theme detail, source document detail, AI evidence detail, static evidence nav.
  - event and theme SQL now link extraction artifacts through either `event_id` or source document `document_id`.
  - event list rows now inherit document-level instrument/theme fallback where a SEC filing event has no direct impact rows.
  - source document and AI evidence detail routes now resolve prefixed external document IDs.
  - static evidence navigation points to `/ai-evidence/ai-evidence-1`.
  - live FastAPI and browser smoke verified event, source document, and evidence pages.
- 진행 중:
  - none.
- 막힌 점:
  - none.

## Exact Next Step

- exact next step: continue local-live-mvp-runtime by selecting the next capped Twelve Data watchlist expansion with `--skip-if-fresh` enabled.

## Verification

- Pending:
- none.
- Passed:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - live API smoke for `/api/events?asOfDate=2024-11-01`, `/api/source-documents/source-document-0000320193-24-000123`, and `/api/ai-evidence/ai-evidence-1`
  - browser smoke for `/events`, `/source-documents/source-document-0000320193-24-000123`, and `/ai-evidence/ai-evidence-1`
  - `git diff --check`

## Risks

- The data quality of extracted AI fields remains limited. This task only fixes linkage/visibility.
- Source document detail still shows local storage/checksum metadata because this is a local live MVP. Production redaction policy remains a separate task.
