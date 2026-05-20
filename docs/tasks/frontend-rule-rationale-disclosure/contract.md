# Task Contract

## Task

- 이름: frontend-rule-rationale-disclosure
- 요청: thesis review rationale에 남아 있는 rule code를 사용자용 설명과 audit metadata로 분리한다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - thesis detail의 "최근 검토 이유" 기본 화면에 `recommendation_bucket_avoid`, `recommendation_action_exclude`, `score_below_0.3500` 같은 rule code가 직접 노출되지 않는다.
  - 기본 화면에는 사람이 읽을 수 있는 signal chip과 안전 문구가 보인다.
  - raw rule code와 원문 change notes는 `AuditMetadata`로 접혀 있어 audit 가능하다.
  - API, DB, thesis review action rule, scoring, trading, scheduler behavior는 변경하지 않는다.

## Scope

- 포함:
  - `apps/web/src/app/theses/[thesisId]/page.tsx`
  - `apps/web/src/app/globals.css`
  - docs plan/task
- 제외:
  - backend DTO shape changes
  - DB migration
  - recommendation/thesis scoring changes
  - review action rule changes
  - AI/RAG generation
  - paper/live order writes
  - scheduler activation

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/theses/[thesisId]/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/plans/2026-05-20-frontend-rule-rationale-disclosure.md`
  - `docs/tasks/frontend-rule-rationale-disclosure/*`

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - browser smoke for `/theses/AAPL-bootstrap-v1`
  - browser click smoke for "검토 rule code 보기"
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task frontend-rule-rationale-disclosure`
  - `git diff --check`

## Done Criteria

- [x] Review change notes are parsed into user-facing reasons and audit metadata.
- [x] Default thesis detail view hides raw rule code.
- [x] Rule code can still be opened through metadata disclosure.
- [x] Browser smoke confirms the new display.
- [x] Verification commands pass.
- [x] Handoff and review are updated.
