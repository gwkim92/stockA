# SEC Filings Ingest

## Goal

이 문서는 SEC submissions API에서 filings 메타데이터를 읽어 `ingest.source_document`에 적재하는 첫 경로를 정의한다.

현재 구현 범위:

- SEC submissions JSON 정규화
- filing metadata -> `ingest.source_document` upsert
- `ops.pipeline_run` 생성과 상태 갱신
- fixture 기반 deterministic 검증

## Why This Step Exists

macro 쪽은 이미 숫자 시계열 ingest가 열려 있다.

다음으로 필요한 것은:

- 비정형 원문 메타데이터 수집
- 공시 기반 이벤트 분석의 시작점
- 이후 event extraction으로 연결할 source document 확보

즉 이 단계는 `시장 숫자 데이터` 다음으로 `공시 문서 메타데이터`를 canonical DB에 들이는 첫 단계다.

## Current Flow

1. CLI가 CIK와 optional fixture path를 받는다.
2. SEC submissions payload에서 recent filing arrays를 읽는다.
3. accession number, form, filing date, primary document를 filing record로 정규화한다.
4. filing metadata를 `ingest.source_document`에 upsert한다.
5. run 결과를 `ops.pipeline_run`에 기록한다.

## CLI

정규화 summary만 확인:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli sec-filings-sync \
  --cik 320193 \
  --submissions-json tests/fixtures/sec_submissions_CIK0000320193.json
```

canonical DB에 적재:

```bash
export STOCKANALYSIS_PSQL_COMMAND="psql postgresql://postgres:postgres@127.0.0.1:5432/stockanalysis"
PYTHONPATH=src python3 -m stockanalysis.ingest.cli sec-filings-upsert \
  --cik 320193
```

## Current Mapping

현재 `source_document` 매핑은 다음과 같다.

- `data_source_id` -> `sec_edgar`
- `external_document_id` -> accession number
- `document_type` -> `filing`
- `title` -> `{form} - {primaryDocDescription or company_name}`
- `url` -> SEC archive primary document URL
- `published_at` -> filing date 기준 timestamptz
- `ingested_by_run_id` -> `ops.pipeline_run.run_id`

## Verification

현재 검증 명령:

```bash
bash scripts/verify_sec_filings_ingest.sh
```

이 검증은:

- docker Postgres migration + seed
- fixture 기반 `sec-filings-upsert`
- `ingest.source_document` row count
- `ingested_by_run_id` 연결
- latest `ops.pipeline_run.status`

를 확인한다.

## Current Limits

아직 구현하지 않은 것:

- filing body/raw artifact 저장
- issuer/instrument mapping
- companyfacts/XBRL facts ingest
- event extraction
- live SEC smoke를 포함한 기본 검증

## Sources

- [SEC EDGAR APIs](https://www.sec.gov/edgar/sec-api-documentation)
- [Accessing EDGAR Data](https://www.sec.gov/edgar/searchedgar/accessing-edgar-data.htm)
- [Developer Resources](https://www.sec.gov/about/developer-resources)

## Next Step

다음으로 자연스러운 확장:

1. `sec-companyfacts-ingest`
2. `sec-filings-event-extraction`
3. `market-data-ingest`
