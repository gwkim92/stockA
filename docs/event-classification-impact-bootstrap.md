# Event Classification Impact Bootstrap

## Goal

이 문서는 SEC event rows를 최소 internal theme taxonomy에 연결하는 첫 bootstrap 경로를 정의한다.

현재 구현 범위:

- pending SEC event discovery
- minimal `internal_theme` taxonomy bootstrap
- `event.event_classification_impact` upsert
- bootstrap pipeline run 기록
- fixture 기반 deterministic 검증

## Why This Step Exists

이제 SEC pipeline은 아래까지 열려 있다.

- filing metadata ingest
- raw artifact fetch
- document -> event extraction
- batch event extraction

다음으로 필요한 것은 이벤트를 분류 노드에 연결해서, 이후 cycle engine과 추천 엔진이 `무슨 테마에 영향을 주는 이벤트인지` 읽을 수 있게 만드는 것이다.

즉 이 단계는 `event -> classification node` 전환의 첫 bootstrap path다.

## Current Taxonomy Bootstrap

현재 bootstrap은 아래 노드를 만든다.

- `PUBLIC_COMPANY_REPORTING` (`theme`)
- `ANNUAL_REPORTING` (`subtheme`)
- `QUARTERLY_REPORTING` (`subtheme`)
- `CURRENT_REPORTING` (`subtheme`)
- `CORPORATE_GOVERNANCE` (`subtheme`)

`PUBLIC_COMPANY_REPORTING -> subtheme` hierarchy edge도 함께 만든다.

## Current Event Mapping

- `sec_annual_report_filed` -> `ANNUAL_REPORTING`
- `sec_quarterly_report_filed` -> `QUARTERLY_REPORTING`
- `sec_current_report_filed` -> `CURRENT_REPORTING`
- `sec_proxy_statement_filed` -> `CORPORATE_GOVERNANCE`
- 기타 SEC filing event -> `PUBLIC_COMPANY_REPORTING`

현재 impact는 전부 `neutral`로 기록한다.

## Pending Discovery Rule

자동 bootstrap discovery는 아래 조건을 만족하는 이벤트를 대상으로 한다.

- `event.dedupe_key like 'sec_edgar:%'`
- `event.event_classification_impact` row가 아직 없음

즉 이미 classification impact가 있는 이벤트는 건너뛴다.

## CLI

```bash
export STOCKANALYSIS_PSQL_COMMAND="psql postgresql://postgres:postgres@127.0.0.1:5432/stockanalysis"
PYTHONPATH=src python3 -m stockanalysis.ingest.cli event-classification-impact-bootstrap \
  --limit 20
```

## Verification

현재 검증 명령:

```bash
bash scripts/verify_event_classification_impact_bootstrap.sh
```

이 검증은:

- docker Postgres migration + seed
- 2건 SEC filing metadata ingest
- 2건 raw fetch
- SEC event batch extract
- classification node 5건 bootstrap
- hierarchy edge 4건 bootstrap
- annual/quarterly classification impact 2건 생성
- latest bootstrap pipeline run status

를 확인한다.

## Current Limits

아직 구현하지 않은 것:

- classification impact retry policy
- instrument impact bootstrap
- richer sector/theme taxonomy
- LLM 기반 semantic node selection
- live SEC smoke를 포함한 기본 검증

## Next Step

다음으로 자연스러운 확장:

1. `event-instrument-impact-bootstrap`
2. `sec-filings-event-retry-policy`
3. `sec-companyfacts-ingest`
