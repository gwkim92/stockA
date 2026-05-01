# SEC Filing Raw Fetch

## Goal

이 문서는 이미 `ingest.source_document`에 적재된 SEC filing metadata에 대해 실제 원문 파일을 내려받고, local artifact 경로와 checksum을 연결하는 첫 raw fetch 경로를 정의한다.

현재 구현 범위:

- `sec_edgar` `source_document` 조회
- filing HTML body fetch 또는 fixture body load
- local artifact 저장
- `raw_storage_uri`, `checksum` update
- `ops.pipeline_run` 기록

## Why This Step Exists

`sec-filings-ingest`는 메타데이터만 적재한다.

다음 단계인 event extraction, 정책/실적 문맥 분석, LLM 기반 공시 해석은 실제 filing 원문이 필요하다.

즉 이 단계는 `metadata only` 상태를 넘어 원문 artifact를 canonical document row에 연결하는 첫 단계다.

## Current Flow

1. CLI가 accession number를 받는다.
2. canonical DB에서 해당 `source_document`를 조회한다.
3. fixture body 또는 `source_document.url`에서 raw filing body를 읽는다.
4. local artifact root 아래에 raw filing 파일을 저장한다.
5. `ingest.source_document.raw_storage_uri`, `checksum`을 갱신한다.
6. 결과를 `ops.pipeline_run`에 기록한다.

## CLI

fixture body로 deterministic 실행:

```bash
export STOCKANALYSIS_PSQL_COMMAND="psql postgresql://postgres:postgres@127.0.0.1:5432/stockanalysis"
PYTHONPATH=src python3 -m stockanalysis.ingest.cli sec-filing-raw-fetch \
  --external-document-id 0000320193-24-000123 \
  --body-file tests/fixtures/sec_filing_aapl_20240928_10k.html
```

live URL에서 fetch:

```bash
export STOCKANALYSIS_SEC_USER_AGENT="stockanalysis-bot contact@example.com"
export STOCKANALYSIS_PSQL_COMMAND="psql postgresql://postgres:postgres@127.0.0.1:5432/stockanalysis"
PYTHONPATH=src python3 -m stockanalysis.ingest.cli sec-filing-raw-fetch \
  --external-document-id 0000320193-24-000123
```

## Current Mapping

현재 raw fetch는 아래 필드만 갱신한다.

- `ingest.source_document.raw_storage_uri` -> local file URI
- `ingest.source_document.checksum` -> SHA-256 hex digest

기존 `ingested_by_run_id`는 유지한다.

이 선택은 metadata ingest lineage를 보존하기 위한 임시 결정이다.

## Verification

현재 검증 명령:

```bash
bash scripts/verify_sec_filing_raw_fetch.sh
```

이 검증은:

- docker Postgres migration + seed
- fixture 기반 `sec-filings-upsert`
- fixture 기반 `sec-filing-raw-fetch`
- `raw_storage_uri`, `checksum` update 확인
- latest `ops.pipeline_run.status` 확인
- artifact file 생성 확인

를 검증한다.

## Current Limits

아직 구현하지 않은 것:

- multiple pending documents batch fetch
- compressed exhibits, PDF, XBRL instance 문서 처리
- raw artifact 별도 lineage table
- live SEC smoke를 포함한 기본 검증
- raw artifact 기반 event extraction

## Next Step

다음으로 자연스러운 확장:

1. `sec-filing-raw-batch-fetch`
2. `sec-filings-event-extraction`
3. `sec-companyfacts-ingest`
