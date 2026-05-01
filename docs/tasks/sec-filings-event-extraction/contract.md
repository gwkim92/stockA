# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: sec-filings-event-extraction
- 요청: raw artifact가 연결된 SEC filing에서 heuristic event를 추출해 `event.event`와 `event.event_document_link`에 적재하는 첫 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `sec-filings-event-extract` CLI가 accession number 기준 raw SEC filing artifact를 읽고 canonical event row와 document link를 생성한다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: 공시를 단순 문서가 아니라 투자 시스템이 사용할 event 객체로 바꿔야 이후 classification impact, thesis review, 추천 논리에 연결할 수 있다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/sec/raw_fetch.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `db/migrations/0002_priority_1_tables.sql`
- 관련 문서:
  - `docs/sec-filings-ingest.md`
  - `docs/sec-filing-raw-fetch.md`
  - `docs/verification-plan.md`
  - `docs/tasks/sec-filing-raw-fetch/handoff.md`
- 이전 결정:
  - raw artifact는 `source_document.raw_storage_uri`로 먼저 연결한다.
  - event extraction 첫 단계는 deterministic heuristic path로 제한한다.
  - instrument/classification impact mapping은 후속 task로 분리한다.

## Scope

- 포함:
  - SEC source_document lookup
  - raw artifact text extraction
  - form type 기반 heuristic event candidate 생성
  - `event.event`, `event.event_document_link` upsert
  - CLI, tests, integration verify, task docs
- 제외:
  - LLM 기반 semantic extraction
  - event impact tables 적재
  - batch extraction
  - companyfacts ingest

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/sec-filings-event-extraction.md`
  - `docs/verification-plan.md`
  - `docs/plans/2026-04-20-sec-filings-event-extraction.md`
  - `docs/tasks/sec-filings-event-extraction/`
  - `docs/tasks/sec-filing-raw-fetch/handoff.md`
  - `scripts/verify_sec_filings_event_extract.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/sec/`
  - `tests/test_ingest_cli.py`
  - `tests/test_sec_event_extract.py`
- 수정 금지 파일:
  - migrations and seeds
  - macro ingest code
- 검증에 사용할 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_sec_filings_event_extract.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task sec-filings-event-extraction`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`

## Deliverables

- 필수 결과물:
  - `src/stockanalysis/ingest/sec/event_extract.py`
  - `tests/test_sec_event_extract.py`
  - `scripts/verify_sec_filings_event_extract.sh`
  - `docs/sec-filings-event-extraction.md`
  - `docs/tasks/sec-filings-event-extraction/contract.md`
  - `docs/tasks/sec-filings-event-extraction/plan.md`
  - `docs/tasks/sec-filings-event-extraction/handoff.md`
- 선택 결과물:
  - `docs/tasks/sec-filings-event-extraction/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] raw SEC filing에서 heuristic event가 생성된다
- [x] `event.event_document_link`가 source document에 연결된다
- [x] fixture 기반 SEC event extraction 검증 경로가 존재한다

## Verification Plan

- 자동 검증: `bash scripts/verify_sec_filings_event_extract.sh`, `awh verify --task sec-filings-event-extraction`, placeholder 검색
- 수동 검증: `docs/sec-filings-event-extraction.md`가 current form mapping과 current limits를 분명히 설명하는지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: unit/integration 검증 통과, event row 생성 확인, readiness 검증 통과

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `sec-filings-event-extract` command와 `src/stockanalysis/ingest/sec/event_extract.py`만 제거하면 기존 raw fetch 경로는 유지된다.

## Open Questions

- 질문: event extraction을 계속 heuristic deterministic path로 둘지, 이후 LLM enrichment를 별도 pipeline으로 둘지
- 답이 없을 때 적용할 임시 가정: 현재는 deterministic event skeleton만 만들고 semantic enrichment는 후속 task로 분리한다.
