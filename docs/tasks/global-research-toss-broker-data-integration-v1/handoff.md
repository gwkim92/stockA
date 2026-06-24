# global-research-toss-broker-data-integration-v1 handoff

## Status

- status: implemented_and_ec2_smoked.
- current status: local implementation, GitHub push, EC2 fast-forward deploy, production build, service restart, API smoke, route smoke, and local tunnel smoke are complete.
- completed: local implementation, focused Python tests, Toss market data tests, frontend typecheck, frontend build, AWH task document requirements, commit `889d4846`, GitHub push, and EC2 deploy.

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
- EC2 `npm --prefix apps/web run build`
- EC2 `sudo systemctl restart stockanalysis-web.service stockanalysis-frontend-api.service`
- EC2 `/api/stocks/AAPL` confirms `analysis_price_source.role=analysis_reference`, `broker_price_source.role=broker_reference`, `broker_price_source.used_for_scoring=false`, and Toss provisional reason label is Korean.
- EC2 route smoke: `/`, `/stocks/AAPL`, `/paper-trading`, `/data-health` all HTTP 200 and render `분석 기준 가격`, `토스증권 브로커 데이터`, `추천 점수 미반영`, `증권사 주문 제출 차단`.
- Local tunnel smoke: `http://127.0.0.1:13000/` HTTP 200.

## Remaining

- Toss broker component를 recommendation score component table에 zero-weight로 저장하는 작업은 별도 scoring task로 남긴다. 이번 작업은 화면/API 의미 정리와 read-only broker reality visibility에 한정했다.
- Toss 계좌 주문 이력과 체결 상세를 더 깊게 보여주는 전용 브로커 현실 상세 화면은 후속 UX 작업으로 분리한다.
- EC2 배포와 route smoke는 완료됐다.

## Next Step

- exact next step: add zero-weight broker execution readiness components without changing total recommendation score or cycle score, then expose those components on recommendation detail and paper-trading.
