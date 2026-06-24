# broker-readiness-zero-weight-copy-reset-v1 Contract

## Task Request

- request: 직전 Toss broker data 통합 이후 남은 작업을 진행한다. Toss broker execution readiness를 추천 상세와 페이퍼 거래에 노출하되 추천 총점·순위·사이클 계산은 바꾸지 않는다. 동시에 투자자가 보는 주요 화면 문구에서 내부 구현어와 애매한 “검토” 표현을 다시 정리한다.

## Goal

- goal: 추천 상세가 `토스증권 브로커 현실`을 zero-weight 점수 구성요소로 보여주고, 주요 투자 화면 문구가 `무엇을 판단해야 하는가`, `왜 중요한가`, `다음 행동`을 바로 말하게 만든다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/signal/recommendation.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/korean-labels.ts`
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/paper-trading/page.tsx`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `apps/web/src/app/market-map/page.tsx`
  - `apps/web/src/app/cycle-map/page.tsx`
  - `apps/web/src/app/ai-evidence/page.tsx`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_recommendation_bootstrap.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/broker-readiness-zero-weight-copy-reset-v1/*`

## Invariants

- Do not change total recommendation score, ranking, bucket, recommended weight, benchmark, portfolio positions, or cycle score.
- Do not enable broker submit, automatic orders, or live trading.
- Do not hide blockers, source limits, failed runs, stale data, or read-only order boundaries.
- Keep operational details available on `/data-health`, but do not leak them into primary investment copy.

## Scope

- Add zero-weight recommendation components:
  - `broker_execution_readiness_score`
  - `broker_liquidity_warning`
  - `broker_price_basis_risk`
- Source those component values from Toss provider comparison, Toss microdata, and Toss warning snapshots when available.
- Add frontend provenance labels for broker reality components.
- Refine high-impact visible copy in home, recommendation detail, paper trading, stock detail, market map, cycle map, AI evidence, and data-health.

## Verification

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_recommendation_bootstrap tests.test_frontend_live_adapter`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task broker-readiness-zero-weight-copy-reset-v1`
