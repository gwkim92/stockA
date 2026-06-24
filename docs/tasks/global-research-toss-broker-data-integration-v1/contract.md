# global-research-toss-broker-data-integration-v1

## Task Request

- request: 기존 글로벌 데이터는 분석 기준 데이터로 유지하고, Toss 데이터는 실제 투자 브로커 현실 데이터로 모델링한다. 화면/API 문구에서 `canonical`, `shadow`를 제거하고 `분석 기준 가격`, `브로커 참고 가격`, `실행 가능 가격`, `검증 중 가격`으로 구분한다. Toss 데이터는 화면과 페이퍼 검증에 즉시 사용하되 추천/사이클 점수 직접 반영은 품질 감사와 feature flag 전까지 막는다.

## Goal

- goal: 종목 상세 API와 투자 화면이 글로벌 분석 기준 가격과 Toss 브로커 데이터를 명확히 구분해서 보여주게 만든다. 이 변경은 추천 scoring weight, cycle calculation, broker live order submit을 바꾸지 않는다.

## Purpose

글로벌 가격 데이터와 Toss 증권 데이터를 같은 가격처럼 보이지 않게 분리한다. 글로벌 데이터는 분석 기준 가격으로 유지하고, Toss 데이터는 실제 브로커 화면과 계좌 현실을 확인하는 브로커 참고 데이터로 표시한다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/frontend-api.ts`
  - `apps/web/src/components/candlestick-chart.tsx`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `apps/web/src/app/paper-trading/page.tsx`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/global-research-toss-broker-data-integration-v1/*`

## Scope

- 종목 API에 분석 기준 가격, 브로커 참고 가격, 검증 중 가격의 역할 정보를 추가한다.
- 기존 `canonical_provider`, `toss_shadow_status` 필드는 호환성을 위해 유지하되, 화면의 투자 판단 영역에서는 직접 노출하지 않는다.
- Toss 최신 저거래량 일봉은 가격 오류가 아니라 미완성 가능성으로 설명한다.
- 종목 차트와 데이터 상태 화면의 Toss 문구를 사용자용 한국어로 정리한다.
- 추천 점수, 사이클 계산 weight, 실거래 주문 제출 경계는 변경하지 않는다.

## Non-Goals

- Toss 데이터를 추천/사이클 점수의 primary input으로 승격하지 않는다.
- broker live order submit을 구현하지 않는다.
- 계좌 secret, 배포 env, scheduler 설치 정책을 변경하지 않는다.
- 기존 market schema나 benchmark/evaluation 기준을 바꾸지 않는다.

## Acceptance Criteria

- `/api/stocks/{symbol}` 응답에 `analysis_price_source`, `broker_price_source`, `validation_price_source`, `used_for_scoring`, `used_for_account`, `used_for_execution`, `price_basis_note`가 포함된다.
- `/stocks/{symbol}` 투자 화면에는 `canonical`, `shadow` 대신 `분석 기준 가격`, `토스증권 브로커 데이터`, `추천 점수 미반영` 같은 문구가 보인다.
- `/data-health` Toss 영역은 운영자 화면으로 유지하되, `canonical/shadow`를 사용자 혼동이 적은 설명으로 대체한다.
- Toss 관련 새 필드는 기존 frontend default/type contract와 호환된다.
- 테스트와 타입 검증을 통과한다.

## Verification

- verification command: `git diff --check`
- verification command: `python3 -m py_compile src/stockanalysis/frontend/live_adapter.py`
- verification command: `PYTHONPATH=src python3 -m unittest tests.test_tossinvest_market_data tests.test_frontend_live_adapter`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task global-research-toss-broker-data-integration-v1`
