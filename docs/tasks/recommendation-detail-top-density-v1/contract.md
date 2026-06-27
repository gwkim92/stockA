# recommendation-detail-top-density-v1 Contract

## Task Request

- request: 추천 상세 화면의 첫 절반이 여전히 카드가 많고 반복적이라 전문 투자 판단서처럼 읽히지 않는다. 상단의 추천 요약, 보유 현실, 판단 순서를 압축해 첫 viewport에서 결론과 다음 행동을 더 빠르게 파악할 수 있게 한다.

## Goal

- goal: `/recommendations/[recommendationId]` 상단이 `큰 결론 + 핵심 지표 + 다음 확인 순서` 중심으로 읽히고, 포지션·평단가·손익·주문 경계는 유지하되 과도한 카드 나열을 줄인다. 회사 주식과 ETF/펀드 구분, backend DTO, 추천 점수, portfolio position, broker/order boundary는 변경하지 않는다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/components/recommendation-executive-brief.tsx`
  - `apps/web/src/components/recommendation-executive-brief.module.css`
  - `apps/web/src/components/recommendation-brief-format.ts`
  - `apps/web/src/components/recommendation-position-reality.tsx`
  - `apps/web/src/components/recommendation-position-reality.module.css`
  - `apps/web/src/components/recommendation-professional-audit-panel.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/_components/RecommendationDecisionFlowPanels.tsx`
  - `apps/web/tests/e2e/investment-workspace.spec.ts`
  - `docs/tasks/recommendation-detail-top-density-v1/*`

## Scope

- Replace the five-card executive brief with a more editorial decision summary and compact metric strip.
- Reduce the position reality section to the investment-relevant fields first: holding status, quantity, average cost, current price, P/L, weight, broker reference, order boundary.
- Remove the separate focus panel from the top flow and fold its first actionable item into the decision waterfall panel.
- Keep deep evidence disclosure sections from the previous task intact.

## Non Goals

- No DB schema changes.
- No backend DTO changes.
- No recommendation score, benchmark, portfolio position, paper validation, or broker/order boundary changes.
- No new external dependency.
- No large `globals.css` expansion.

## User-Facing Rules

- Investor-visible copy must avoid `pipeline`, `runner`, `artifact`, `fallback`, `canonical`, `shadow`, raw snake_case, `검토 가능`, `확인한다`, `봐야 한다`, `미수집`.
- Use Korean investor language: conclusion, risk, evidence, position reality, and action boundary.
- Preserve price, average cost, P/L, holding status, and order boundary visibility.
- Mobile 375px must have no horizontal overflow.

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm test`
- verification command: `cd apps/web && npm run build`
- verification command: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13009 npm run test:e2e`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-detail-top-density-v1`

## Acceptance Criteria

- Recommendation detail renders without the separate focus-panel block.
- Executive brief shows a single dominant conclusion area and compact metrics, not five equal cards.
- Position section exposes holding quantity, average cost, current price, unrealized P/L, recommended weight, broker reference, and order boundary without a dense 8-card grid.
- Decision waterfall includes a clear next-check callout.
- Local and EC2 route smoke for `/recommendations/AAPL-2024-11-01` returns 200.
