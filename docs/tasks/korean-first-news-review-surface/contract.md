# Task Contract

## Task

- 이름: korean-first-news-review-surface
- 요청: 뉴스 원문 대조와 AI 근거 검토 화면에서 영어 제목을 기본 본문으로 노출하지 않고 한국어 검토 요약을 먼저 보여준다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 뉴스 카드와 원천 문서 화면은 한국어 사용자가 영어를 먼저 읽지 않아도 검토 흐름을 이해할 수 있어야 한다. 영어 원문 제목은 숨기지 않되 보조 정보로 접어두고, 기본 화면에는 종목/테마/방향/영향도 기반의 한국어 해석을 우선 표시한다.

## Scope

- 포함:
  - `NewsTitleBlock` 한국어 우선 표시
  - 원천 문서 상세의 한국어 검토 요약 강화
  - 필요한 CSS 보강
  - task handoff/review
  - EC2 렌더링 검증
- 제외:
  - DB schema 변경
  - 실제 번역 컬럼 저장
  - Codex OAuth 번역 배치 구현
  - 유료 번역 API 도입

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/components/news-title-block.tsx`
  - `apps/web/src/app/source-documents/[documentId]/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/korean-first-news-review-surface/*`

## Verification Commands

- 검증에 사용할 명령:
  - `git diff --check`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task korean-first-news-review-surface`
  - Browser text/screenshot check for `http://127.0.0.1:13000/ai-evidence/ai-evidence-251`
  - Browser text/screenshot check for one `/source-documents/...` page

## Done Criteria

- [ ] 뉴스 카드 기본 라벨이 `원문 제목`이 아니라 `한국어 확인` 또는 동등한 사용자 문장이다.
- [ ] 영어 제목은 접힌 `영어 원문 제목` 영역에서 확인할 수 있다.
- [ ] 원천 문서 상세 첫 화면에 한국어 검토 요약이 보인다.
- [ ] typecheck/build/AWH/browser smoke가 통과한다.
