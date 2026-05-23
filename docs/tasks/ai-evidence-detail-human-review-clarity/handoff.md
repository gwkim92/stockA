# Session Handoff

## Current Status

- 상태: in_progress
- in progress: `/ai-evidence/[evidenceId]` 상세 화면을 사람이 실제로 검토할 수 있는 구조로 재정리한다.
- 기준일: 2026-05-23

## Findings

- `ai-evidence-251`은 뉴스 묶음 증거인데 상단 대상이 `SPY`로 먼저 보여 사용자가 검토 대상을 종목으로 오해한다.
- “AI가 한 일”, “추천 사용” 같은 설명은 많지만, 사람이 확인해야 할 질문과 이동 버튼이 선명하지 않다.
- 현재 서비스는 read-only라 완료/반려 저장은 범위 밖이지만, 원천 대조/종목 맥락/추천 검토서 이동은 바로 제공할 수 있다.

## Exact Next Step

- exact next step: 뉴스 묶음 상세 상단을 `검토 질문 + 판정 + 이동 버튼` 구조로 바꾸고, 종목 연결을 후보 맥락으로 분리한다.
