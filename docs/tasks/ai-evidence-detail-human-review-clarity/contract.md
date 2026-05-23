# Task Contract

## Task

- 이름: ai-evidence-detail-human-review-clarity
- 요청: `/ai-evidence/[evidenceId]` 상세 화면에서 사람이 무엇을 검토해야 하는지 즉시 이해되게 고친다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 뉴스 묶음 증거 상세는 종목이 아니라 `뉴스 묶음/테마`를 검토 대상으로 먼저 보여주고, 연결 종목은 후보 맥락으로 분리한다. 상단에는 “이 페이지에서 판단할 질문”, “현재 판정”, “원천 대조/종목 맥락/추천 검토서” 이동 버튼이 있어야 하며, 사람 검토가 무엇을 의미하는지 사용자 문장으로 설명해야 한다.

## Scope

- 포함:
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx` 정보 구조와 문구 수정
  - 필요한 CSS 보강
  - task handoff/review
  - 로컬/EC2 화면 검증
- 제외:
  - write API 추가
  - 검토 완료/반려 저장 기능
  - DB schema 변경
  - AI/provider/scheduler 변경

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/ai-evidence-detail-human-review-clarity/*`

## Verification Commands

- 검증에 사용할 명령:
  - `git diff --check`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task ai-evidence-detail-human-review-clarity`
  - Browser text/screenshot check for `http://127.0.0.1:13000/ai-evidence/ai-evidence-251` after deploy

## Done Criteria

- [ ] `ai-evidence-251` 상단 대상이 `SPY`가 아니라 `금리·연준 뉴스 묶음`으로 보인다.
- [ ] `SPY`는 연결 종목 후보/맥락으로 분리되어 보인다.
- [ ] 원천 대조, 종목 맥락, 추천 검토서 이동 버튼이 상단에 있다.
- [ ] “무엇을 검토해야 하는지”가 3-4개의 명확한 질문으로 보인다.
- [ ] typecheck/build/AWH/browser smoke가 통과한다.
