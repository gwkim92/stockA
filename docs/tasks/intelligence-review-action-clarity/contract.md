# Task Contract

## Task

- 이름: intelligence-review-action-clarity
- request: `/intelligence` 페이지가 무엇을 보여주고 사용자가 무엇을 검토해야 하는지 이해되도록 재구성한다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/intelligence` 상단에서 오늘 검토할 항목과 검토 시작 버튼이 바로 보이고, “사람 검토”가 필요한 곳에서 무엇을 어떤 순서로 어느 화면에서 확인해야 하는지 명확하다. read-only 경계 때문에 아직 저장형 승인/반려 버튼이 없다는 사실을 숨기지 않고 사용자 문장으로 설명하며, 뉴스 묶음 카드에서 묶인 기준, 종목 관계, 검토 체크리스트, 다음 이동 버튼이 한 번에 보여야 한다.

## Scope

- 포함:
  - `apps/web/src/app/intelligence/page.tsx` 정보 구조와 문구 수정
  - 필요한 CSS 보강
  - task handoff/review
  - 로컬/EC2 화면 검증
- 제외:
  - write API 추가
  - DB schema 변경
  - 실제 승인/반려 저장 기능
  - AI/provider/scheduler 변경

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/intelligence/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/intelligence-review-action-clarity/*`

## Acceptance Criteria

- `/intelligence`에 “검토 시작” CTA가 보인다.
- 페이지가 “묶음”, “개별 뉴스 후보”, “추천 연결”, “차단 후보” 검토를 구분해 설명한다.
- 각 뉴스 묶음 카드에 검토 체크리스트와 실행 가능한 링크가 있다.
- “검토 완료/반려 저장 버튼은 아직 없다”는 상태가 사용자에게 숨겨지지 않는다.
- Next typecheck/build와 `/intelligence` 브라우저 렌더링 검증이 통과한다.

## Verification Commands

- 검증에 사용할 명령:
  - `git diff --check`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task intelligence-review-action-clarity`
  - Browser text/screenshot check for `http://127.0.0.1:13000/intelligence` after deploy
