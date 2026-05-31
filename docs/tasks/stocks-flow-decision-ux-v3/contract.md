# stocks-flow-decision-ux-v3

## Task Request

- request: `/stocks`와 `/stocks/[symbol]`을 이어서 점검하고 종목별 판단 흐름을 사용자 관점으로 정리한다.

## Goal

- goal: 종목 화면을 `종목 선택 → 현재 판단 상태 → 가격/보유/추천 → 기업·재무·밸류에이션 → 뉴스와 상위 흐름 → 가상 매매/실거래 차단` 순서로 읽게 만든다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/stocks/page.tsx`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `apps/web/src/components/valuation-target-range-card.tsx`
  - `docs/tasks/stocks-flow-decision-ux-v3/*`

## Non-Goals

- API contract, DB schema, scheduler, AI batch, ingest 로직은 변경하지 않는다.
- 추천 점수 weight, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- 실거래 주문 또는 쓰기 기능을 추가하지 않는다.

## Acceptance Criteria

- `/stocks`에서 종목을 왜 열어야 하는지와 어떤 버튼을 눌러야 하는지 명확하다.
- `/stocks/[symbol]`에서 `thesis`, `source blocker`, `RAG`, `runner`, `broker`, `paper validation` 같은 내부 용어가 주요 사용자 문구로 노출되지 않는다.
- 투자 판단 화면은 “주문 불가/읽기 전용” 경계를 유지하되 개발자 로그처럼 보이지 않는다.
- `/stocks`, `/stocks/SPY`, `/stocks/AAPL` route smoke가 200을 반환한다.
- Next.js typecheck/build, AWH verify, diff check를 통과한다.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task stocks-flow-decision-ux-v3`
- verification command: `git diff --check`
- verification command: EC2 route/content smoke for `/stocks`, `/stocks/SPY`, `/stocks/AAPL`

## Boundaries

- 추천 결과나 투자 판단 산식은 건드리지 않는다.
- 원천 데이터 부족, 가상 검증 차단, 실거래 차단은 숨기지 않는다. 단, 사람이 이해할 수 있는 말로 바꿔 표시한다.
