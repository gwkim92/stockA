# Thesis Review Bootstrap

이 문서는 active investment thesis를 현재 linked recommendation과 cycle evidence 기준으로 검토해 `signal.thesis_review`에 저장하는 경로를 설명한다.

## Goal

- source:
  - `signal.recommendation_batch`
  - `signal.recommendation`
  - `signal.investment_thesis`
  - `signal.cycle_state_snapshot`
  - `signal.instrument_feature_value`
- target:
  - `signal.thesis_review`

이 단계의 목적은 최초 thesis를 만든 뒤에도 계속 잘 투자하고 있는지 검토 가능한 이력을 남기는 것이다.

## CLI

```bash
STOCKANALYSIS_PSQL_COMMAND="psql -U postgres -d stockanalysis" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli thesis-review-bootstrap \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --review-version bootstrap-v1
```

## Current Input Rule

현재 bootstrap은 보수적이다.

- selected recommendation batch 기준
- active recommendation만 대상
- non-null `recommendation.thesis_id`만 대상
- linked `signal.investment_thesis.status = active`만 대상
- current cycle snapshot과 market features는 있으면 review evidence로 붙인다
- 같은 `(thesis_id, review_date, review_source)`는 update-or-insert 한다

## Review Rule

현재 review는 deterministic rule이다.

- cycle state가 `structurally_broken`이면 action `exit`
- recommendation bucket/action이 `avoid`/`exclude`이거나 total score가 `0.3500` 미만이면 action `exit`
- cycle state가 `correcting`이면 action `reduce`
- bucket/action이 `watch`이면 action `watch`
- 그 외는 action `keep`

Health score는 recommendation total score를 기본값으로 쓰고, action이 `exit`이면 최대 `0.2500`, `reduce`이면 최대 `0.4500`으로 제한한다.

## Review Cadence

- `exit`, `reduce`: 7일 뒤 재검토
- `watch`: 30일 뒤 재검토
- `keep`, `add`: 90일 뒤 재검토

현재 fixture chain에서는 AAPL thesis review가 action `watch`, health score `0.3610`, next review date `2024-12-01`로 생성된다.

## Boundary

- AI는 review summary를 생성하지 않는다.
- thesis status는 자동 변경하지 않는다.
- portfolio execution 또는 실거래는 범위 밖이다.
- portfolio position 없이 linked recommendation/thesis만 검토한다.

## Verification

- `bash /Users/woody/ai/stockanalysis/scripts/verify_thesis_review_bootstrap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task thesis-review-bootstrap`

현재 Docker verify는 아래를 이어 실행한다.

```text
market-universe-bootstrap
-> market-price-universe-backfill
-> strategy-universe-slice
-> market-feature-snapshot
-> sec-filings-upsert
-> sec-filing-raw-fetch
-> sec-filings-event-extract
-> event-classification-impact-bootstrap
-> event-instrument-impact-bootstrap
-> instrument-theme-enrichment
-> cycle-state-snapshot
-> recommendation-bootstrap
-> thesis-bootstrap
-> thesis-review-bootstrap
```

그리고 `signal.thesis_review` table 존재, review 1건, AAPL review action `watch`, health score `0.3610`, next review date `2024-12-01`, latest `thesis_review_bootstrap` pipeline run status 성공을 확인한다.

## Next Step

1. `recommendation-score-component`
2. `portfolio-review-bootstrap`
3. `live OpenAI Responses provider`
