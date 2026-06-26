# recommendation-detail-professional-redesign-v1 Contract

## Request

- `/recommendations/[id]`를 전문 투자 판단서 구조로 재구성한다.

## Scope

- Split route-local components under `apps/web/src/app/recommendations/[recommendationId]/_components/`.
- Company stock layout: 투자 결론, 가격·수익률, 재무 품질, 밸류에이션, 산업·피어, 뉴스·AI, 사이클, thesis, 포지션 현실, 가상 검증.
- ETF/fund layout: 투자 결론, 구성종목, 벤치마크 추적, 비용률, NAV 괴리, 유동성, 시장·사이클 영향, 포지션 현실.

## Invariants

- No recommendation weight change.
- No backend API/schema change.
- No broker submit or automatic order path.

## Verification

- `/recommendations/<live-id>` shows distinct company/fund structure.
- No investor-facing forbidden terms.
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `cd apps/web && npm run test:e2e`
- AWH verify for this task.
