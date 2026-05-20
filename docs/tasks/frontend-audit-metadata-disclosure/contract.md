# Task Contract

## Task

- 이름: frontend-audit-metadata-disclosure
- 요청: 사용자 화면에 직접 노출되는 감사/추적용 ID를 접힌 metadata로 낮춘다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 추천 상세의 점수 근거 카드에서 `market-feature-*`, `universe-rank-*`, `pipeline-run-*`가 기본 화면에 직접 노출되지 않는다.
  - 투자 논리 상세의 근거 카드에서 `performance-outcome-*`, `event-*`가 기본 화면에 직접 노출되지 않는다.
  - 원천 링크가 있으면 "AI 근거 열기", "원천 이벤트 열기"처럼 의미 있는 링크 라벨을 보여준다.
  - raw ID는 삭제하지 않고 `<details>` 기반 추적 메타데이터로 확인 가능하다.
  - API, DB, score/action rule, trading, scheduler behavior는 변경하지 않는다.

## Scope

- 포함:
  - `apps/web/src/components/audit-metadata.tsx`
  - `apps/web/src/app/globals.css`
  - `apps/web/src/app/theses/[thesisId]/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - docs plan/task
- 제외:
  - backend DTO shape changes
  - DB migration
  - data ingest
  - recommendation scoring/action changes
  - AI/RAG generation
  - paper/live order writes
  - scheduler activation

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/components/audit-metadata.tsx`
  - `apps/web/src/app/globals.css`
  - `apps/web/src/app/theses/[thesisId]/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `docs/plans/2026-05-20-frontend-audit-metadata-disclosure.md`
  - `docs/tasks/frontend-audit-metadata-disclosure/*`

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - browser smoke for `/theses/AAPL-bootstrap-v1`
  - browser smoke for `/recommendations/AAPL-2024-11-01`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task frontend-audit-metadata-disclosure`
  - `git diff --check`

## Done Criteria

- [x] Shared audit metadata component exists and handles long values without overflow.
- [x] Recommendation detail uses meaningful links/labels first and moves raw IDs into metadata.
- [x] Thesis detail uses meaningful links/labels first and moves raw IDs into metadata.
- [x] Browser smoke confirms the default view is less technical while metadata remains accessible.
- [x] Verification commands pass.
- [x] Handoff and review are updated.
