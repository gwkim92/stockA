# events-copy-polish-v3 handoff

## Status

- current status: completed.
- completed: task contract created.
- completed: `/events`, `/events/classification`, and shared news cards no longer expose the targeted jargon in the main rendered flow.
- completed: EC2 deployment and route/content smoke passed.

## Changes

- changed `AI evidence` wording to `AI 판단` / `AI 판단 상세`.
- changed `validator` wording to `검증` / `검증 차단`.
- changed `rule pack` wording to `기본 규칙`.
- changed `exposure` wording to `종목 민감도`.
- changed news card action labels to `AI 판단 상세`, `차단 이유 보기`, `구조화 결과 보기`, and `원문 열기`.
- kept existing source document, AI evidence, stock, and theme links unchanged.

## Verification

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task events-copy-polish-v3`
- passed: `git diff --check`
- passed: EC2 deploy from `origin/codex/local-mvp-runtime-aws-bootstrap`, Next build, and `stockanalysis-web.service` restart.
- passed: `http://127.0.0.1:13000/events` returned 200 and contained `뉴스 이벤트 판정판`, `검증 통과`, `AI 판단`, `원문 열기` with no `validator`, `AI evidence`, `rule pack`, or `exposure`.
- passed: `http://127.0.0.1:13000/events/classification` returned 200 and contained `1차 분류 판정판`, `기본 규칙`, `검증을 통과`, `종목 민감도` with no targeted jargon.
- passed: Playwright snapshot smoke for both routes found required Korean terms and no targeted jargon.

## Exact Next Step

- exact next step: continue the page-by-page UX refactor with `/cycles`, focusing on cycle status, evidence, and recommendation impact wording.

## Notes

- frontend visibility only.
- AI extraction, validator, event classification, recommendation, and order logic are not changed.
- commit: `ab30bec9`.
