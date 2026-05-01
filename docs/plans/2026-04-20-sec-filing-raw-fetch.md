# 2026-04-20 sec-filing-raw-fetch

## Objective

이미 적재된 SEC filing metadata row에 raw filing artifact와 checksum을 연결하는 첫 canonical 경로를 만든다.

## Scope

- `source_document` lookup
- raw filing fixture/live fetch
- artifact write
- `raw_storage_uri`, `checksum` update
- CLI, tests, verify script, task docs

## Non-Goals

- batch fetch
- companyfacts ingest
- event extraction
- raw artifact 전용 새 테이블

## Validation

- unit test 통과
- `bash scripts/verify_sec_filing_raw_fetch.sh` 통과
- `awh verify --task sec-filing-raw-fetch` 통과
