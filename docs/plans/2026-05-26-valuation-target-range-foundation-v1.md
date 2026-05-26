# Valuation Target Range Foundation V1

## Summary

기존 `market.valuation_snapshot`을 종목, 추천, Thesis 상세 판단 흐름에 노출한다. 투자자는 현재가와 목표가 범위, 상승여지, 안전마진, 사용된 방법을 한 화면에서 확인해야 한다.

## Implementation Plan

1. Stock/recommendation/thesis live state SQL에 최신 valuation snapshot rows를 추가한다.
2. Python live adapter에 `valuation_target_range` 정규화 helper를 추가한다.
3. Recommendation professional decision waterfall의 valuation step에 목표가 범위 fact를 연결한다.
4. TypeScript DTO에 `ValuationTargetRange` 타입을 추가한다.
5. 종목, 추천, Thesis 페이지에 한국어 target range card를 추가한다.
6. Unit, typecheck, build, roadmap/AWH verifier를 실행한다.

## Guardrails

- Recommendation score와 weight는 변경하지 않는다.
- Broker/order boundary는 계속 read-only로 유지한다.
- API 응답에는 secret이나 DB connection 정보를 포함하지 않는다.

## Test Plan

- `tests.test_frontend_live_adapter` focused tests
- full Python unittest
- `python -m compileall src tests`
- `cd apps/web && npm run typecheck && npm run build`
- `bash scripts/verify_project_execution_roadmap.sh`
- `awh verify --task valuation-target-range-foundation-v1`

