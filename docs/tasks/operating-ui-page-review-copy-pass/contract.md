# Task Contract

## Task

- 이름: operating-ui-page-review-copy-pass
- 요청: 전체 페이지를 다시 점검하고, 사용자가 무엇을 봐야 하는지 흐리는 남은 문구와 raw 제목 표시를 고친다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 주요 route가 200으로 응답하는지 점검된다.
  - 추천 상세와 원천 문서 상세에서 원문 제목과 한국어 해석이 분리된다.
  - 남은 페이지별 UX 문제와 다음 수정 우선순위가 handoff에 기록된다.
  - schema, 추천 산식, scheduler, secrets는 변경하지 않는다.

## Scope

- 포함:
  - `/recommendations/[id]` copy/근거 표시 보강
  - `/source-documents/[id]` copy/원문 제목 표시 보강
  - 주요 route HTTP smoke
  - task handoff에 전체 페이지 점검 결과 기록
- 제외:
  - DB/API contract 변경
  - LLM 번역 batch 추가
  - 추천 점수 산식 변경
  - 실거래/broker submit 변경

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/recommendations/page.tsx`
  - `apps/web/src/app/source-documents/[documentId]/page.tsx`
  - `apps/web/src/app/stocks/page.tsx`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `apps/web/src/app/performance/page.tsx`
  - `apps/web/src/app/paper-trading/page.tsx`
  - `apps/web/src/app/theses/[thesisId]/page.tsx`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `docs/tasks/operating-ui-page-review-copy-pass/*`
- 수정 금지 파일:
  - DB migrations/schema
  - backend API contract
  - scheduler cadence
  - secrets/env files
  - recommendation scoring

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task operating-ui-page-review-copy-pass`

## Done Criteria

- [ ] 추천 상세 raw 뉴스 제목 표시가 원문/해석 구조로 바뀐다.
- [ ] 원천 문서 상세 raw 제목 표시가 원문/해석 구조로 바뀐다.
- [ ] 주요 route smoke가 기록된다.
- [ ] 페이지별 남은 문제와 다음 순서가 기록된다.
- [ ] 로컬 검증이 통과한다.
- [ ] EC2 배포와 smoke가 통과한다.
