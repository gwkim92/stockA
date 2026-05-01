# Event Instrument Impact Bootstrap

## Goal

이 문서는 pending SEC event를 canonical instrument에 연결하는 첫 bootstrap 경로를 정의한다.

현재 구현 범위:

- pending SEC event discovery
- event title/summary 기반 company name 추출
- exact-match canonical instrument lookup
- `event.event_instrument_impact` upsert
- bootstrap pipeline run 기록
- fixture 기반 deterministic 검증

## Why This Step Exists

이제 SEC pipeline은 아래까지 열려 있다.

- filing metadata ingest
- raw artifact fetch
- document -> event extraction
- batch event extraction
- classification impact bootstrap

다음으로 필요한 것은 이벤트를 실제 투자 대상 종목과 연결하는 것이다.

즉 이 단계는 `event -> canonical instrument` 전환의 첫 bootstrap path다.

## Pending Discovery Rule

자동 bootstrap discovery는 아래 조건을 만족하는 이벤트를 대상으로 한다.

- `event.dedupe_key like 'sec_edgar:%'`
- `event.event_instrument_impact` row가 아직 없음

즉 이미 instrument impact가 있는 이벤트는 건너뛴다.

## Current Resolution Rule

현재 canonical instrument lookup은 아주 보수적으로 동작한다.

- event title의 `:` 뒤 company name 우선 추출
- 실패하면 summary의 `filed SEC Form` 앞 company name 사용
- `ref.issuer.display_name`
- `ref.issuer.legal_name`
- `ref.instrument.name`

위 세 필드와 company name이 case-insensitive exact match일 때만 연결한다.

현재 impact 기본값:

- `sec_annual_report_filed` -> `neutral`, strength `0.75`, confidence `0.95`
- `sec_quarterly_report_filed` -> `neutral`, strength `0.70`, confidence `0.94`
- `sec_current_report_filed` -> `neutral`, strength `0.80`, confidence `0.93`
- `sec_proxy_statement_filed` -> `neutral`, strength `0.60`, confidence `0.92`
- 기타 SEC filing event -> `neutral`, strength `0.60`, confidence `0.85`

## CLI

```bash
export STOCKANALYSIS_PSQL_COMMAND="psql postgresql://postgres:postgres@127.0.0.1:5432/stockanalysis"
PYTHONPATH=src python3 -m stockanalysis.ingest.cli event-instrument-impact-bootstrap \
  --limit 20
```

## Verification

현재 검증 명령:

```bash
bash scripts/verify_event_instrument_impact_bootstrap.sh
```

이 검증은:

- docker Postgres migration + seed
- 2건 SEC filing metadata ingest
- 2건 raw fetch
- SEC event batch extract
- canonical Apple issuer/instrument insert
- annual/quarterly SEC event 2건의 `event.event_instrument_impact` 생성
- latest bootstrap pipeline run status

를 확인한다.

## Current Limits

아직 구현하지 않은 것:

- fuzzy matching이나 alias resolution
- issuer master bootstrap
- event-instrument impact retry policy
- multi-instrument impact expansion
- live SEC smoke를 포함한 기본 검증

## Next Step

다음으로 자연스러운 확장:

1. `sec-companyfacts-ingest`
2. `sec-filings-event-retry-policy`
3. market universe/price ingest
