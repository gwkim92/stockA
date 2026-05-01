# SEC Filings Event Extraction

## Goal

이 문서는 raw artifact가 연결된 SEC filing에서 deterministic heuristic event를 추출해 `event.event`와 `event.event_document_link`에 적재하는 첫 경로를 정의한다.

현재 구현 범위:

- `sec_edgar` `source_document` lookup
- raw filing artifact text 추출
- form type 기반 heuristic event candidate 생성
- `event.event`, `event.event_document_link` upsert
- `ops.pipeline_run` 기록

## Why This Step Exists

`sec-filings-ingest`는 metadata를 적재하고, `sec-filing-raw-fetch`는 원문 artifact를 연결한다.

다음으로 필요한 것은 공시를 그냥 저장하는 것이 아니라, 투자 시스템이 사용할 `이벤트 객체`로 바꾸는 것이다.

즉 이 단계는 `document -> event` 전환의 첫 deterministic path다.

## Current Flow

1. CLI가 accession number를 받는다.
2. canonical DB에서 raw artifact가 연결된 `source_document` row를 조회한다.
3. raw HTML/text artifact에서 본문 텍스트를 추출한다.
4. filing form type과 본문 excerpt를 조합해 heuristic event candidate를 만든다.
5. `event.event`를 dedupe key 기준으로 upsert한다.
6. `event.event_document_link`에 source link를 남긴다.
7. 결과를 `ops.pipeline_run`에 기록한다.

## Current Mapping

현재 form type 매핑은 다음과 같다.

- `10-K` -> `sec_annual_report_filed`
- `10-Q` -> `sec_quarterly_report_filed`
- `8-K` -> `sec_current_report_filed`
- `DEF 14A` -> `sec_proxy_statement_filed`
- 그 외 -> `sec_filing_recorded`

현재 구현은 filing 자체를 `neutral` 이벤트로 기록한다.

`event.document_link.link_type`는 `source`로 고정한다.

## CLI

```bash
export STOCKANALYSIS_PSQL_COMMAND="psql postgresql://postgres:postgres@127.0.0.1:5432/stockanalysis"
PYTHONPATH=src python3 -m stockanalysis.ingest.cli sec-filings-event-extract \
  --external-document-id 0000320193-24-000123
```

## Verification

현재 검증 명령:

```bash
bash scripts/verify_sec_filings_event_extract.sh
```

이 검증은:

- docker Postgres migration + seed
- fixture 기반 `sec-filings-upsert`
- fixture 기반 `sec-filing-raw-fetch`
- fixture 기반 `sec-filings-event-extract`
- `event.event` row 생성
- `event.event_document_link` 연결
- latest `ops.pipeline_run.status`

를 확인한다.

## Current Limits

아직 구현하지 않은 것:

- LLM 기반 semantic extraction
- event classification impact/instrument impact 생성
- batch pending event extraction
- live SEC smoke를 포함한 기본 검증
- 8-K item 세분화와 sentiment/polarity 해석

## Next Step

다음으로 자연스러운 확장:

1. `event-classification-impact-bootstrap`
2. `sec-filings-event-retry-policy`
3. `sec-companyfacts-ingest`
