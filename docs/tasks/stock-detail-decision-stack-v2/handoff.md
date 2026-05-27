# stock-detail-decision-stack-v2 Handoff

## Status

- in progress: 종목 상세 상단의 판단 순서와 다음 클릭 위치를 정리하는 작업을 진행 중이다.

## Completed

- completed: task contract를 생성했다.
- completed: `/stocks/[symbol]` hero 직후 `현재 결론` 패널을 추가했다.
- completed: 추천, 보유, 뉴스·상위 흐름, thesis, 페이퍼·주문 상태를 분리한 카드와 CTA를 추가했다.
- completed: 가격, 추천/보유, 상위 흐름, 직접 뉴스 섹션의 읽는 순서와 제목을 명확히 바꿨다.
- completed: 모바일에서 결론 패널과 카드가 한 열로 내려가도록 CSS를 추가했다.

## Boundaries

- recommendation weight, scoring formula, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- API, DB schema, scheduler, AI batch는 변경하지 않는다.

## Verification Log

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task stock-detail-decision-stack-v2`
- passed: `git diff --check`
- pending: EC2/local tunnel `/stocks/SPY` route smoke

## Next Step

- exact next step: 변경사항을 commit/push/deploy한 뒤 EC2/local tunnel `/stocks/SPY` route smoke로 새 결론 패널과 문구를 확인한다.
