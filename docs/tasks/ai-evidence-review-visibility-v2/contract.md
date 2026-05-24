# Task Contract

## Task

- 이름: ai-evidence-review-visibility-v2
- 요청: 원천 뉴스, 한국어 번역, AI 구조화 결과, validator 통과/차단 이유, 추천 연결을 한 화면에서 추적 가능하게 정리한다.
- 담당: Codex
- 날짜: 2026-05-24

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/ai-evidence/[evidenceId]`에서 `원천 -> 번역 -> AI 구조화 -> validator 판정 -> 종목/추천 연결` 경로가 상단에서 한 번에 보인다.

## Scope

- 포함:
  - AI 근거 상세에 추적 경로 패널 추가
  - validator 통과/차단 상태를 사람이 읽는 문장으로 표시
  - 추천/종목/원천 문서 링크를 trace card에 연결
  - 기존 원천 뉴스, 구조화 필드, 종목 맥락 섹션은 유지
- 제외:
  - AI 재분석 실행
  - validator 판정 로직 변경
  - canonical event impact write
  - 추천 scoring 변경
  - 저장형 승인/반려 UI

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/ai-evidence-review-visibility-v2/*`
- 수정 금지 파일:
  - AI extraction runner
  - validator logic
  - recommendation scoring
  - DB migrations
  - broker/order submit path

## Verification

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task ai-evidence-review-visibility-v2`

## Done Criteria

- AI 근거 상세 상단에서 원천, 번역, AI 구조화, validator, 추천 연결이 순서대로 보인다.
- 한국어 번역이 있으면 원문보다 먼저 보인다.
- 차단 후보는 추천 입력으로 쓰지 않는다고 명확히 표시한다.
- 추천 연결이 없으면 "연결 없음"을 오류처럼 보이지 않게 설명한다.
