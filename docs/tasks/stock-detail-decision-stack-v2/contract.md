# stock-detail-decision-stack-v2 Contract

## Task Request

- request: 종목 상세 화면에서 가격, 뉴스, 상위 흐름, 추천, 보유, 페이퍼 상태가 어떤 순서로 읽혀야 하는지 명확히 한다.

## Goal

- goal: `/stocks/{symbol}` 첫 화면에서 현재 결론, 차단 여부, 추천/보유/뉴스/페이퍼 상태, 다음 클릭 위치를 한눈에 볼 수 있다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/stock-detail-decision-stack-v2/*`

## Invariants

- 추천 scoring formula, recommendation weights, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- API, DB schema, scheduler, AI batch는 변경하지 않는다.
- 화면은 저장된 read-only 데이터만 보여주며 실시간 AI 호출이나 주문 생성을 하지 않는다.

## Scope

- 종목 상세 hero 직후 “현재 결론” 패널을 추가한다.
- 추천, 보유, 뉴스/상위 흐름, 페이퍼 상태를 한 패널에서 분리해 보여준다.
- 사용자가 다음에 눌러야 할 위치를 `추천 근거`, `투자 논리`, `뉴스/흐름`, `페이퍼 거래 상태`로 명확히 제공한다.
- 가격, 추천/보유, 상위 흐름, 직접 뉴스 섹션에 읽는 순서를 드러내는 앵커와 문구를 보강한다.
- 모바일에서 결론 카드가 한 열로 자연스럽게 내려오도록 CSS를 추가한다.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task stock-detail-decision-stack-v2`
- verification command: `git diff --check`
- verification command: EC2/local tunnel route smoke for `/stocks/SPY`

## Done Criteria

- [x] `/stocks/SPY`에 `현재 결론` 패널이 렌더링된다.
- [x] 결론 패널에서 추천, 보유, 뉴스/흐름, 페이퍼 상태가 분리되어 보인다.
- [x] 추천이나 thesis가 있으면 해당 상세로 이동하는 버튼이 보인다.
- [x] 페이퍼 거래 상태와 주문 차단 경계가 명확히 보인다.
- [x] local verification과 EC2 route smoke가 통과한다.
