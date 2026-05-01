# SEC Filings Event Batch Extract

## Goal

이 문서는 raw artifact가 연결된 여러 SEC filing을 한 번에 event로 변환하는 첫 batch extraction 경로를 정의한다.

현재 구현 범위:

- pending SEC filing discovery
- explicit accession override 또는 자동 pending selection
- single-document event extractor 재사용
- success/failure summary 집계
- fixture 기반 deterministic 검증

## Why This Step Exists

`sec-filings-event-extraction`는 single-document path만 연다.

실제 운영에서는 raw artifact가 쌓일 때마다 문서 하나씩 처리하는 것이 아니라, pending filing들을 한 번에 이벤트화해야 한다.

즉 이 단계는 `single document -> batch queue` 확장이다.

## Current Flow

1. CLI가 optional accession list와 `limit`를 받는다.
2. accession list가 없으면 `raw_storage_uri`가 있고 아직 `source` event link가 없는 SEC 문서를 조회한다.
3. 문서마다 기존 `sec-filings-event-extract`를 호출한다.
4. 문서별 success/failure를 summary JSON으로 반환한다.

## Pending Discovery Rule

자동 batch discovery는 아래 조건을 만족하는 문서를 대상으로 한다.

- `sec_edgar` source document
- `raw_storage_uri is not null`
- `external_document_id is not null`
- `event.event_document_link(link_type='source')`가 아직 없음

즉 이미 event로 연결된 문서는 중복 처리하지 않는다.

## CLI

pending 문서 자동 처리:

```bash
export STOCKANALYSIS_PSQL_COMMAND="psql postgresql://postgres:postgres@127.0.0.1:5432/stockanalysis"
PYTHONPATH=src python3 -m stockanalysis.ingest.cli sec-filings-event-batch-extract \
  --limit 20
```

특정 accession만 강제 처리:

```bash
export STOCKANALYSIS_PSQL_COMMAND="psql postgresql://postgres:postgres@127.0.0.1:5432/stockanalysis"
PYTHONPATH=src python3 -m stockanalysis.ingest.cli sec-filings-event-batch-extract \
  --external-document-id 0000320193-24-000123 \
  --external-document-id 0000320193-24-000101
```

## Verification

현재 검증 명령:

```bash
bash scripts/verify_sec_filings_event_batch_extract.sh
```

이 검증은:

- docker Postgres migration + seed
- fixture 기반 `sec-filings-upsert`
- 2건 raw filing artifact fetch
- `sec-filings-event-batch-extract`
- 2건 linked event row
- annual/quarterly dedupe key 확인
- succeeded `sec_filings_event_extract` run count 확인

를 검증한다.

## Current Limits

아직 구현하지 않은 것:

- parent batch pipeline run
- retry policy와 dead-letter queue
- LLM 기반 semantic event enrichment
- classification/instrument impact mapping
- live SEC smoke를 포함한 기본 검증

## Next Step

다음으로 자연스러운 확장:

1. `event-instrument-impact-bootstrap`
2. `sec-filings-event-retry-policy`
3. `sec-companyfacts-ingest`
