# Session Handoff

## Current Status

- 상태: completed
- 완료: `/ai-evidence/[evidenceId]` 상세 화면을 사람이 실제로 검토할 수 있는 구조로 재정리했다.
- 기준일: 2026-05-23

## Findings

- `ai-evidence-251`은 뉴스 묶음 증거인데 상단 대상이 `SPY`로 먼저 보여 사용자가 검토 대상을 종목으로 오해한다.
- “AI가 한 일”, “추천 사용” 같은 설명은 많지만, 사람이 확인해야 할 질문과 이동 버튼이 선명하지 않다.
- 현재 서비스는 read-only라 완료/반려 저장은 범위 밖이지만, 원천 대조/종목 맥락/추천 검토서 이동은 바로 제공할 수 있다.
- 수정 후 `ai-evidence-251`의 상단 검토 대상은 `금리·연준 뉴스 묶음`이고, `SPY`는 연결 종목 후보로 분리된다.
- 화면 상단에 원천 대조, 종목 맥락, 추천 검토서 이동 버튼을 배치했다.

## Exact Next Step

- exact next step: 저장형 검토가 필요하면 `review approval/write boundary` task를 만들어 완료/반려, 검토자, 감사 로그를 구현한다.
