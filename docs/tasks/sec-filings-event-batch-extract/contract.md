# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: sec-filings-event-batch-extract
- 요청: raw artifact가 연결된 여러 SEC filing을 batch로 event화하는 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `sec-filings-event-batch-extract` CLI가 pending SEC raw filings를 찾아 기존 single-document extractor를 통해 event row와 source link를 생성한다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: 운영 환경에서는 SEC 공시를 문서마다 수동 호출할 수 없으므로, pending filing을 queue처럼 batch 처리하는 경로가 필요하다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/sec/event_extract.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `scripts/verify_sec_filings_event_extract.sh`
- 관련 문서:
  - `docs/sec-filings-event-extraction.md`
  - `docs/verification-plan.md`
  - `docs/tasks/sec-filings-event-extraction/handoff.md`
- 이전 결정:
  - single-document extractor는 `sec_filings_event_extract` pipeline run을 남긴다.
  - dedupe key는 `sec_edgar:{accession}:{event_type}` 형식으로 고정한다.
  - batch는 pending discovery와 집계만 담당하고 per-document worker를 재사용한다.

## Scope

- 포함:
  - pending SEC document discovery
  - explicit accession override 또는 자동 pending batch
  - batch summary 집계
  - CLI, tests, integration verify, task docs
- 제외:
  - parent batch pipeline run
  - retry queue
  - classification/instrument impact mapping
  - companyfacts ingest

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/sec-filings-event-batch-extract.md`
  - `docs/verification-plan.md`
  - `docs/plans/2026-04-20-sec-filings-event-batch-extract.md`
  - `docs/tasks/sec-filings-event-batch-extract/`
  - `docs/tasks/sec-filings-event-extraction/handoff.md`
  - `scripts/verify_sec_filings_event_batch_extract.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/sec/event_extract.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_sec_event_extract.py`
  - `tests/fixtures/sec_filing_aapl_20240629_10q.html`
- 수정 금지 파일:
  - migrations and seeds
  - macro ingest code
- 검증에 사용할 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_sec_filings_event_batch_extract.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task sec-filings-event-batch-extract`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`

## Deliverables

- 필수 결과물:
  - `scripts/verify_sec_filings_event_batch_extract.sh`
  - `docs/sec-filings-event-batch-extract.md`
  - `docs/tasks/sec-filings-event-batch-extract/contract.md`
  - `docs/tasks/sec-filings-event-batch-extract/plan.md`
  - `docs/tasks/sec-filings-event-batch-extract/handoff.md`
- 선택 결과물:
  - `docs/tasks/sec-filings-event-batch-extract/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] pending SEC raw filing을 batch로 event화할 수 있다
- [x] 2건 batch verify 경로가 존재한다
- [x] 실패 문서를 제외하고 나머지 문서 처리를 계속할 수 있다

## Verification Plan

- 자동 검증: `bash scripts/verify_sec_filings_event_batch_extract.sh`, `awh verify --task sec-filings-event-batch-extract`, placeholder 검색
- 수동 검증: `docs/sec-filings-event-batch-extract.md`가 pending discovery rule과 current limits를 분명히 설명하는지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: unit/integration 검증 통과, 2건 event linkage 확인, readiness 검증 통과

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `sec-filings-event-batch-extract` command와 pending discovery 코드만 제거하면 single-document extractor는 유지된다.

## Open Questions

- 질문: batch parent run과 retry policy를 별도 테이블/파이프라인으로 둘지
- 답이 없을 때 적용할 임시 가정: 현재는 per-document pipeline run만 남기고 batch 자체는 summary JSON으로만 처리한다.
