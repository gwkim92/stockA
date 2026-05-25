# Session Handoff

## Current Status

- 완료: 포트폴리오 위험 예산 v2 로컬 구현과 계약/타입/빌드/AWH, EC2 API/route smoke를 통과했다.

## Implementation Notes

- 목표: 포트폴리오 화면을 단일 종목 상한 확인에서 섹터/테마 집중도와 리밸런싱 우선순위까지 보는 read-only 위험 예산 화면으로 확장한다.
- API 필드: `/api/portfolio/{portfolio}/coverage` payload의 `risk_budget.concentration`, `risk_budget.rebalance_priorities`.
- 화면 섹션:
  - `섹터·테마 집중도`
  - `리밸런싱 우선순위`
- 입력:
  - `portfolio.position_snapshot`
  - `ref.instrument`
  - `ref.instrument_classification_membership`
  - `ref.classification_node`
  - 기존 `portfolio.allocation_policy`
- 정책 fallback:
  - 단일 종목 상한: 기존 `portfolio.allocation_policy.max_single_position_weight`
  - 리밸런싱 하한: 기존 `portfolio.allocation_policy.min_rebalance_target_weight`
  - 섹터 한도: 45%
  - 테마 한도: 40%
  - 미분류 한도: 10%
- 경계:
  - 추천 weight는 바꾸지 않는다.
  - 자동 리밸런싱/주문 실행은 하지 않는다.
  - classification이 없는 노출은 데이터 품질 gap으로 표시한다.

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- Passed: `cd apps/web && npm run typecheck`
- Passed: `cd apps/web && npm run build`
- Passed: `git diff --check`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-risk-budget-policy-v2`
- Passed on EC2: pulled `e92c6da`, rebuilt `apps/web`, restarted `stockanalysis-frontend-api.service` and `stockanalysis-web.service`.
- Passed on EC2 service check: both services returned `active`.
- Passed on EC2 API: `/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2026-05-25` returned effective `as_of=2026-05-23`, risk status `needs_position_review`, concentration status `needs_concentration_review`, sector exposure count `0`, theme exposure count `4`, unclassified weight `0.2271`, rebalance priorities `8`.
- Passed on EC2 API: review reasons included `over_single_position_limit:MSFT`, `over_single_position_limit:TSLA`, `theme_over_limit:US_MARKET_BREADTH`, `classification_gap_weight_over_limit`, `sector_classification_missing`.
- Passed on EC2 route smoke: `/portfolio/coverage` rendered `섹터·테마 집중도`, `리밸런싱 우선순위`, `한 종목이 아니라 같은 흐름`, `섹터 분류가 아직 없다`, `테마 노출`, `초과 그룹`, `바로 주문하지 않고`.

## Exact Next Step

- exact next step: 다음 작업은 `sector-classification-enrichment-v1`로 현재 EC2에서 드러난 sector exposure count `0` 문제를 해소하거나, `frontend-equity-research-experience-v2`로 종목/추천 상세를 전문 리서치 리포트 순서로 더 정리한다.
