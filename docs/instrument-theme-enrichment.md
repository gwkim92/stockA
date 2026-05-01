# Instrument Theme Enrichment

이 문서는 selected strategy universe instruments를 existing event impact evidence와 연결해 internal theme memberships를 만드는 첫 bootstrap 경로를 설명한다.

## Goal

- source:
  - `signal.strategy_universe_batch`
  - `signal.strategy_universe_member`
  - `event.event_instrument_impact`
  - `event.event_classification_impact`
- target:
  - `ref.instrument_classification_membership`

이 단계의 목적은 instrument와 classification node 사이의 최소 연결을 만드는 것이다. 그래야 다음 단계인 cycle-state-snapshot이 node를 기준으로 계산되고, 이후 thesis/recommendation이 instrument-theme 관계를 읽을 수 있다.

## Current Rule

현재 bootstrap은 아주 보수적이다.

- selected strategy universe instruments만 대상
- `internal_theme` taxonomy만 대상
- event가 instrument와 node 모두에 연결된 경우만 membership 생성
- membership type은 `derived_theme`
- direct event-linked node만 연결

즉 현재는 `event -> instrument`, `event -> classification`이 둘 다 있는 경우에만 `instrument -> classification membership`이 생긴다.

## CLI

```bash
STOCKANALYSIS_PSQL_COMMAND="psql -U postgres -d stockanalysis" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli instrument-theme-enrichment \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1
```

## Stored Fields

`ref.instrument_classification_membership`에 아래가 저장된다.

- `instrument_id`
- `node_id`
- `membership_type = 'derived_theme'`
- `confidence`
- `source_document_id`
- `valid_from = earliest supporting event date`
- `valid_to = null`

## Current Limits

- parent theme propagation은 아직 없다.
- sector/industry enrichment는 아직 없다.
- event coverage가 적으면 membership coverage도 낮다.
- evidence는 현재 table 구조상 `source_document_id`와 date/confidence 수준만 남긴다.

## Verification

- `bash /Users/woody/ai/stockanalysis/scripts/verify_instrument_theme_enrichment.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task instrument-theme-enrichment`

현재 Docker verify는 아래를 이어 실행한다.

```text
market-universe-bootstrap
-> market-price-universe-backfill
-> strategy-universe-slice
-> sec-filings-upsert
-> sec-filing-raw-fetch
-> sec-filings-event-extract
-> event-classification-impact-bootstrap
-> event-instrument-impact-bootstrap
-> instrument-theme-enrichment
```

그리고 `AAPL -> ANNUAL_REPORTING` membership 1건과 latest pipeline run status 성공을 확인한다.

## Current Downstream

현재 이 경로의 직접 후속 단계는 `cycle-state-snapshot`이다.

## Next Step

1. `recommendation-bootstrap`
2. `live OpenAI Responses provider`
3. broader theme/sector propagation
