# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: sec-filing-raw-fetch
- 요청: 이미 적재된 SEC filing metadata row에 raw artifact와 checksum을 연결하는 first raw fetch 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `sec-filing-raw-fetch` CLI가 accession number 기준 `ingest.source_document`를 조회하고 raw filing artifact를 저장한 뒤 `raw_storage_uri`, `checksum`을 canonical DB에 반영한다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: 메타데이터만으로는 공시 본문 분석과 event extraction을 할 수 없으므로, 실제 filing 원문 artifact를 연결해야 다음 단계로 갈 수 있다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/http.py`
  - `src/stockanalysis/ingest/psql.py`
  - `src/stockanalysis/ingest/sec/`
- 관련 문서:
  - `docs/sec-filings-ingest.md`
  - `docs/verification-plan.md`
  - `docs/tasks/sec-filings-ingest/handoff.md`
- 이전 결정:
  - `source_document`는 비정형 원문 메타데이터의 canonical row다.
  - raw artifact는 기존 row의 `raw_storage_uri`, `checksum`으로 먼저 연결한다.
  - metadata ingest lineage는 보존하고 raw fetch는 별도 pipeline run으로 남긴다.

## Scope

- 포함:
  - `source_document` lookup
  - raw filing fixture/live fetch
  - local artifact write
  - `raw_storage_uri`, `checksum` update
  - CLI, tests, integration verify, task docs
- 제외:
  - batch raw fetch
  - event extraction
  - companyfacts ingest
  - raw artifact 전용 새 테이블

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/sec-filing-raw-fetch.md`
  - `docs/verification-plan.md`
  - `docs/plans/2026-04-20-sec-filing-raw-fetch.md`
  - `docs/tasks/sec-filing-raw-fetch/`
  - `docs/tasks/sec-filings-ingest/handoff.md`
  - `scripts/verify_sec_filing_raw_fetch.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/sec/`
  - `tests/test_ingest_cli.py`
  - `tests/test_sec_raw_fetch.py`
  - `tests/fixtures/sec_filing_aapl_20240928_10k.html`
- 수정 금지 파일:
  - migrations and seeds
  - macro ingest code
- 검증에 사용할 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_sec_filing_raw_fetch.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task sec-filing-raw-fetch`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`

## Deliverables

- 필수 결과물:
  - `src/stockanalysis/ingest/sec/raw_fetch.py`
  - `tests/test_sec_raw_fetch.py`
  - `scripts/verify_sec_filing_raw_fetch.sh`
  - `docs/sec-filing-raw-fetch.md`
  - `docs/tasks/sec-filing-raw-fetch/contract.md`
  - `docs/tasks/sec-filing-raw-fetch/plan.md`
  - `docs/tasks/sec-filing-raw-fetch/handoff.md`
- 선택 결과물:
  - `docs/tasks/sec-filing-raw-fetch/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] raw filing artifact가 local path에 저장된다
- [x] `raw_storage_uri`, `checksum`이 canonical DB에 반영된다
- [x] fixture 기반 raw fetch 검증 경로가 존재한다

## Verification Plan

- 자동 검증: `bash scripts/verify_sec_filing_raw_fetch.sh`, `awh verify --task sec-filing-raw-fetch`, placeholder 검색
- 수동 검증: `docs/sec-filing-raw-fetch.md`가 current update mapping과 current limits를 분명히 설명하는지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: unit/integration 검증 통과, `raw_storage_uri`/`checksum` update 확인, readiness 검증 통과

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `sec-filing-raw-fetch` command와 `src/stockanalysis/ingest/sec/raw_fetch.py`만 제거하면 기존 filings metadata ingest는 유지된다.

## Open Questions

- 질문: raw artifact lineage를 계속 `source_document` row update로 표현할지, 별도 artifact table을 둘지
- 답이 없을 때 적용할 임시 가정: 현재는 기존 row update로 먼저 경로를 열고 richer lineage는 후속 task로 분리한다.
