# Task Contract

## Task

- 이름: frontend-domain-language-normalization
- 요청: 화면에 남은 내부 코드/영어 도메인 표현을 한국어 운영 문구로 바꾼다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - thesis 상세 화면의 hero, 검토 이유, 핵심 주장, 무효화 조건에 남은 주요 raw code가 한국어로 보인다.
  - recommendation 상세 화면의 strategy/version/action 주요 code가 한국어로 보인다.
  - 공통 helper에서 문장 내부 code token을 안전하게 치환한다.
  - API, DB, 추천 rule, scoring, trading, scheduler behavior는 변경하지 않는다.

## Scope

- 포함:
  - `apps/web/src/lib/korean-labels.ts`
  - `apps/web/src/app/theses/[thesisId]/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - docs plan/task
- 제외:
  - backend DTO shape changes
  - DB migration
  - data ingest
  - score/action logic
  - AI/RAG generation
  - paper/live order writes
  - scheduler activation

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/lib/korean-labels.ts`
  - `apps/web/src/app/theses/[thesisId]/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `docs/plans/2026-05-20-frontend-domain-language-normalization.md`
  - `docs/tasks/frontend-domain-language-normalization/*`

## Verification Commands

- 검증에 사용할 명령:
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- browser smoke for `/theses/AAPL-bootstrap-v1`
- browser smoke for `/recommendations/AAPL-2024-11-01`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task frontend-domain-language-normalization`
- `git diff --check`

## Done Criteria

- [x] Common label helper translates embedded raw tokens in long Korean/English mixed sentences.
- [x] Thesis detail no longer shows obvious raw `long_term_core`, `avoid`, `exclude`, `ANNUAL_REPORTING`, `forming`, `unavailable` in primary copy when mappings exist.
- [x] Recommendation detail version/action labels use Korean labels where mappings exist.
- [x] Browser smoke confirms improved wording on live pages.
- [x] Verification commands pass.
- [x] Handoff and review are updated.
