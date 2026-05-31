# stocks-flow-decision-ux-v3 Handoff

## Status

- in_progress: `/stocks`와 `/stocks/[symbol]` UX copy/refactor를 구현했고 EC2 반영 전이다.

## Completed

- completed: task contract를 생성했다.
- completed: `/stocks` hero, 우선순위 카드, 종목 목록 안내를 사용자용 한국어로 다듬었다.
- completed: `/stocks/[symbol]`의 현재 결론, 투자 판단 사용 여부, 뉴스/흐름 연결, 투자 논리, 가상 매매/실거래 상태 문구를 정리했다.
- completed: 종목 상세에서 같이 렌더링되는 밸류에이션 카드의 `forecast`, `SOTP`, `footnote`, `True`, `proxy` 같은 내부 표현을 사용자용 한국어로 치환했다.
- completed: 추천 산식, 포트폴리오, DB/API, scheduler, AI batch, 실거래 주문 경계는 변경하지 않았다.

## Boundaries

- recommendation weight, scoring formula, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- API, DB schema, scheduler, AI batch는 변경하지 않는다.

## Verification Log

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task stocks-flow-decision-ux-v3`
- passed: `git diff --check`
- pending: EC2 deploy and route smoke.

## Next Step

- exact next step: `/stocks`, `/stocks/[symbol]`, `valuation-target-range-card` visible copy를 정리하고 검증한다.
