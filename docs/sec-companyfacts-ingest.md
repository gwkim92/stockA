# SEC Companyfacts Ingest

## Goal

이 문서는 SEC `companyfacts` JSON에서 selected 재무 팩트를 읽어 canonical financial schema에 적재하는 첫 경로를 정의한다.

현재 구현 범위:

- SEC companyfacts JSON 정규화
- selected `us-gaap` USD duration metrics ingest
- exact-match canonical instrument lookup
- `market.financial_statement_period` upsert
- `market.financial_metric_value` upsert
- fixture 기반 deterministic 검증

## Why This Step Exists

SEC pipeline은 이제 문서, 이벤트, classification, instrument impact까지 열려 있다.

다음으로 필요한 것은 기업 재무 팩트를 canonical schema에 넣어서 이후 thesis, recommendation, review 엔진이 펀더멘털을 바로 읽게 만드는 것이다.

즉 이 단계는 `SEC XBRL facts -> canonical financial tables` 전환의 첫 ingest path다.

## Current Flow

1. CLI가 CIK와 optional companyfacts fixture path를 받는다.
2. companyfacts payload에서 selected `us-gaap` concepts를 읽는다.
3. `entityName` 기준으로 canonical instrument exact-match lookup을 수행한다.
4. 10-K/10-Q duration facts를 `financial_statement_period`와 `financial_metric_value`로 적재한다.
5. run 결과를 `ops.pipeline_run`에 기록한다.

## Current Metric Map

현재 selected metric은 다음만 지원한다.

- `Revenues` -> `revenue`
- `RevenueFromContractWithCustomerExcludingAssessedTax` -> `revenue`
- `NetIncomeLoss` -> `net_income`
- `OperatingIncomeLoss` -> `operating_income`
- `NetCashProvidedByUsedInOperatingActivities` -> `operating_cash_flow`

현재 필터 규칙:

- `facts.us-gaap`만 사용
- unit이 `USD`인 fact만 사용
- `10-K`, `10-Q`만 사용
- `start`, `end`, `val`, `fy`가 있는 duration fact만 사용

즉 instant balance sheet facts나 비-USD units는 아직 넣지 않는다.

## CLI

canonical DB에 적재:

```bash
export STOCKANALYSIS_PSQL_COMMAND="psql postgresql://postgres:postgres@127.0.0.1:5432/stockanalysis"
PYTHONPATH=src python3 -m stockanalysis.ingest.cli sec-companyfacts-upsert \
  --cik 320193
```

fixture 기반 적재:

```bash
export STOCKANALYSIS_PSQL_COMMAND="psql postgresql://postgres:postgres@127.0.0.1:5432/stockanalysis"
PYTHONPATH=src python3 -m stockanalysis.ingest.cli sec-companyfacts-upsert \
  --cik 320193 \
  --companyfacts-json tests/fixtures/sec_companyfacts_CIK0000320193.json
```

## Canonical Mapping

현재 canonical mapping은 다음과 같다.

- instrument resolution -> `ref.issuer.display_name`, `ref.issuer.legal_name`, `ref.instrument.name` exact match
- annual/quarterly period -> `market.financial_statement_period`
- metric value -> `market.financial_metric_value`
- SEC accession number -> optional `ingest.source_document.external_document_id` linkage
- current source run -> `ops.pipeline_run.run_id`

## Verification

현재 검증 명령:

```bash
bash scripts/verify_sec_companyfacts_ingest.sh
```

이 검증은:

- docker Postgres migration + seed
- SEC filing metadata ingest
- canonical Apple issuer/instrument insert
- fixture 기반 companyfacts upsert
- annual/quarterly period row 2건
- metric row 4건
- source document linkage 2건
- latest `sec_companyfacts_upsert` run status

를 확인한다.

## Current Limits

아직 구현하지 않은 것:

- instant balance sheet fact ingest
- IFRS concept ingest
- fuzzy instrument resolution
- estimate snapshot generation
- earnings revision or factor engine 연결
- live SEC smoke를 포함한 기본 검증

## Next Step

다음으로 자연스러운 확장:

1. `market-price-ingest`
2. `sec-filings-event-retry-policy`
3. richer financial concept coverage
