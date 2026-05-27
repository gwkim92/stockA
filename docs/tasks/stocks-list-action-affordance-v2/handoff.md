# stocks-list-action-affordance-v2 Handoff

## Status

- in progress: `/stocks` 화면의 종목 상세 진입 affordance를 명확히 하는 작업을 진행 중이다.

## Completed

- completed: task contract를 생성했다.
- completed: `/stocks` hero 문구를 종목 선택과 상세 분석 진입 목적에 맞게 수정했다.
- completed: 추천·보유 연결이 있는 종목을 우선 보여주는 “오늘 먼저 볼 종목” 섹션을 추가했다.
- completed: 종목 목록 테이블에 `상세 확인` 열과 `종목 상세 보기`, `추천 근거 보기` 버튼을 추가했다.
- completed: 행 전체가 링크가 아니라 종목명과 버튼만 이동 대상이라는 안내 문구를 추가했다.
- completed: 모바일에서 액션 버튼이 전체 폭으로 보이도록 CSS를 보정했다.

## Boundaries

- recommendation weight, scoring formula, benchmark, portfolio position, broker/order flow는 변경하지 않았다.
- API, DB schema, scheduler, AI batch는 변경하지 않았다.

## Verification Log

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task stocks-list-action-affordance-v2`
- passed: `git diff --check`
- pending: EC2/local tunnel `/stocks` route smoke

## Next Step

- exact next step: 변경사항을 commit/push/deploy한 뒤 EC2/local tunnel `/stocks` route smoke로 새 문구와 버튼 렌더링을 확인한다.
