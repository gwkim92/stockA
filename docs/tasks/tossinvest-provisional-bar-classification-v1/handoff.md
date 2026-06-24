# tossinvest-provisional-bar-classification-v1 Handoff

## Completed

- Root cause 확인:
  - 2026-06-23 Toss/canonical comparison의 conflict 30건은 수집 누락이 아니라 최신 Toss bar의 저거래량 provisional 상태였다.
  - 6/18, 6/22 가격은 거의 동일했고, 6/23 Toss 거래량만 canonical 대비 극단적으로 작았다.
- 구현:
  - `src/stockanalysis/operations/tossinvest_market_data.py`
  - `TOSSINVEST_PROVISIONAL_VOLUME_RATIO_THRESHOLD = Decimal("0.10")`
  - provisional bar는 diff aggregate에서 제외하고, 존재 시 `shadow_collecting / toss_provisional_low_volume_bar`로 분류한다.
  - `evidence_json`에 `provisional_compared_bar_count`, `provisional_volume_ratio_threshold`를 저장한다.
- 테스트:
  - `tests/test_tossinvest_market_data.py`에 SQL policy assertion 추가.

## EC2 Verification

- Deployed commit: `72bd02b2`
- Runner: `tossinvest-provider-comparison-run`, `run_id=7279`
- Final DB:
  - `TOSS_CANDLE_SUMMARY={"rows": 1377, "symbols": 46, "max_trade_date": "2026-06-24", "min_trade_date": "2026-05-11"}`
  - `CANONICAL_2026_06_23_SUMMARY={"missing_symbols": 0, "tracked_symbols": 46, "symbols_with_canonical_bar": 46}`
  - `COMPARISON_STATUS_COUNTS=[{"count": 7, "status": "candidate_ready"}, {"count": 39, "status": "shadow_collecting"}]`
  - `COMPARISON_REASON_COUNTS=[{"count": 39, "reason": "toss_provisional_low_volume_bar"}, {"count": 7, "reason": "within_diff_threshold"}]`
  - `COMPARISON_BAD_STATES=[]`
  - `TOSS_RUNNING_PIPELINES=[]`
- Route smoke:
  - FastAPI `http://127.0.0.1:8787/__ready` -> 200
  - Next `http://127.0.0.1:3000/` -> 200

## Remaining

- 다음 정상 장마감 이후 Toss latest bar가 충분한 거래량으로 갱신되면 shadow rows가 `candidate_ready`로 자연 전환되는지 확인한다.
- 필요하면 `/data-health`에 `toss_provisional_low_volume_bar`를 사용자용 문구로 노출한다.
