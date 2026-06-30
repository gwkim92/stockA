# toss-broker-visibility-v1 Contract

## Task Request

- request: Toss 데이터가 수집되고 있어도 화면에서 어디에 쓰이는지, 왜 추천 점수에는 아직 쓰이지 않는지, 토스증권 기준 가격이 글로벌 분석 기준 가격과 어떻게 다른지 알기 어렵다. 종목 상세와 추천 상세에서 Toss를 "브로커 현실 데이터"로 명확히 보여주고, 투자자 화면의 내부 용어 노출을 줄인다.

## Goal

- goal: 토스증권 데이터를 분석 기준 가격과 혼동하지 않도록 투자자 화면에 "브로커 현실 데이터"로 표시한다. 종목 상세와 추천 상세에서 토스 데이터가 계좌·브로커 검증에는 쓰이지만 추천 점수에는 직접 반영되지 않는다는 경계를 명확히 한다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/lib/presentation/broker.ts`
  - `apps/web/src/lib/presentation/index.ts`
  - `apps/web/src/lib/presentation/research-view-models.test.ts`
  - `apps/web/src/app/stocks/[symbol]/_components/StockPriceAndMarketSections.tsx`
  - `apps/web/src/components/recommendation-broker-reality.tsx`
  - `apps/web/src/components/recommendation-position-reality.tsx`
  - `apps/web/src/components/recommendation-position-reality.module.css`
  - `apps/web/src/components/recommendation-executive-brief.tsx`
  - `apps/web/src/components/recommendation-executive-brief.module.css`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/globals.css`
  - `apps/web/src/lib/korean-labels.ts`
  - `apps/web/src/app/cycle-map/page.tsx`
  - `docs/tasks/toss-broker-visibility-v1/*`

## Scope

- `/stocks/[symbol]` 가격·시장 섹션에 토스증권 브로커 현실 카드를 추가한다.
- 추천 상세의 포지션 현실 영역에 토스 계좌/가격/주문 경계를 별도 컴포넌트로 분리한다.
- `canonical`, `shadow`, raw relation code처럼 투자자 화면에 새어 나오던 내부 표현을 한국어 표현으로 정리한다.
- 구형 요약 추천 기록과 전문 추천 기록의 렌더링 분기를 명확히 한다.

## Non Goals

- 추천 점수 weight 변경 없음.
- DB schema 변경 없음.
- Toss 데이터를 추천/사이클 공식 입력으로 승격하지 않음.
- 실거래 주문 제출 구현 없음.

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm test`
- verification command: `cd apps/web && npm run build`
- verification command: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13004 npm run test:e2e`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task toss-broker-visibility-v1`
- verification command: EC2 live route smoke for `/`, `/data-health`, `/stocks/AAPL`, `/paper-trading`, `/cycle-map`, live recommendation detail.
