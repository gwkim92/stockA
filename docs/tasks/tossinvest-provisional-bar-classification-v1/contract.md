# tossinvest-provisional-bar-classification-v1

## Objective

TossInvest shadow price comparison에서 최신 일봉이 아직 완성되지 않은 저거래량 provisional bar인 경우를 가격 충돌로 오판하지 않도록 분류한다.

## Scope

- `tossinvest-provider-comparison-run`의 비교 SQL에 provisional compared bar 감지를 추가한다.
- canonical 거래량 대비 Toss 거래량이 10% 미만인 matched bar는 diff 계산에서 제외한다.
- provisional bar가 있으면 `conflict_review_required`가 아니라 `shadow_collecting`으로 유지한다.
- reason은 `toss_provisional_low_volume_bar`로 저장한다.
- canonical promotion, broker submit, recommendation scoring weight는 변경하지 않는다.

## Evidence

- EC2에서 2026-06-23 비교 기준 conflict 30건은 모두 최신 Toss bar의 거래량이 canonical 대비 10% 미만이었다.
- 해당 low-volume bar를 제외하면 conflict 30건 모두 최대 종가 차이가 50bps 이하로 내려갔다.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_tossinvest_market_data`
- `git diff --check`
- EC2 `tossinvest-provider-comparison-run --comparison-date 2026-06-23 --execute`
- EC2 final DB check:
  - Toss candles: 46 symbols, 1377 rows
  - canonical 2026-06-23 bars: 46/46
  - comparison: `candidate_ready=7`, `shadow_collecting=39`, `missing=0`, `conflict_review_required=0`
  - reason counts: `toss_provisional_low_volume_bar=39`, `within_diff_threshold=7`
  - FastAPI ready HTTP 200, Next home HTTP 200

## Non-Goals

- Toss shadow 데이터를 canonical로 승격하지 않는다.
- 수집 주기나 systemd timer를 활성화하지 않는다.
- 실거래, 주문, broker flow는 변경하지 않는다.
