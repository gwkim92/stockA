# global-research-toss-broker-data-integration-v1 handoff

## Status

- status: implemented_locally.
- current status: local implementation and verification complete. EC2 deployment smoke is still pending until the changes are committed, pushed to `develop`, pulled on EC2, and route-smoked.
- completed: local implementation, focused Python tests, Toss market data tests, frontend typecheck, frontend build, and AWH task document requirements.

## Implemented

- `/api/stocks/{symbol}` stock detail payload에 가격 역할을 추가했다.
  - `analysis_price_source`: 추천·사이클·성과 계산에 쓰는 분석 기준 가격
  - `broker_price_source`: 토스증권 계좌·호가 현실 확인용 브로커 데이터
  - `validation_price_source`: 분석 기준 가격과 토스 가격을 비교하는 검증 중 가격
- 기존 `canonical_provider`, `toss_shadow_status`는 하위 호환을 위해 유지했다.
- Toss 최신 저거래량 일봉 사유를 `최신 토스 일봉 미완성 가능성`으로 설명하는 label 변환을 추가했다.
- 종목 차트와 종목 상세 가격 카드에서 `canonical/shadow` 대신 `분석 기준 가격`, `토스증권 브로커 데이터`, `추천 점수 미반영`을 표시한다.
- 페이퍼 거래 화면에 토스증권 read-only 브로커 현실 카드(매수 여력, 매도 가능 수량, 호가·체결 종목 수)를 추가했다.
- `/data-health` Toss 영역은 운영자 화면으로 유지하되, `provider evidence`, `shadow`, `canonical` 설명을 사용자 이해 가능한 한국어로 대체했다.

## Verification

- `git diff --check`
- `python3 -m py_compile src/stockanalysis/frontend/live_adapter.py`
- `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_toss_provider_evidence_labels_provisional_latest_bar_as_incomplete_broker_data tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_stock_detail_response_matches_frontend_contract_shape`
- `PYTHONPATH=src python3 -m unittest tests.test_tossinvest_market_data tests.test_frontend_live_adapter`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`

## Remaining

- Toss broker component를 recommendation score component table에 zero-weight로 저장하는 작업은 별도 scoring task로 남긴다. 이번 작업은 화면/API 의미 정리와 read-only broker reality visibility에 한정했다.
- Toss 계좌 주문 이력과 체결 상세를 더 깊게 보여주는 전용 브로커 현실 상세 화면은 후속 UX 작업으로 분리한다.
- EC2 배포 후 route smoke에서 `/stocks/AAPL`, `/paper-trading`, `/data-health` 문구를 확인해야 한다.

## Next Step

- exact next step: commit and push this task to `develop`, then deploy to EC2 with `git pull --ff-only origin develop`, restart FastAPI/Next, and smoke `/api/stocks/AAPL`, `/stocks/AAPL`, `/paper-trading`, `/data-health`.
