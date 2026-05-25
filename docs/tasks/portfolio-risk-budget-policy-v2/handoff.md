# Session Handoff

## Current Status

- 완료: 포트폴리오 위험 예산 v2 로컬 구현과 계약/타입/빌드/AWH 검증을 통과했다.

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

## Exact Next Step

- exact next step: Git commit/push 후 EC2에 fast-forward 배포하고, `/api/portfolio/Long%20Term%20Paper/coverage`와 `/portfolio/coverage`에서 집중도와 리밸런싱 우선순위가 보이는지 smoke 검증한다.
