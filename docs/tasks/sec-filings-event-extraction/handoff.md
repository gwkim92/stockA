# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: sec-filings-event-extraction
- 담당: Codex
- 날짜: 2026-04-20

## Current Status

- 완료:
  - `sec-filings-event-extraction` task 문서를 생성했다.
  - heuristic event extraction 코드, CLI, 테스트, verify script를 구현했다.
  - raw SEC filing artifact에서 `event.event`와 `event.event_document_link`를 만드는 single-document path를 추가했다.
  - unit test, docker 기반 integration verify, readiness 검증을 통과했다.
- 진행 중:
  - 없음.
- 막힌 점:
  - 없음.

## Files Touched

- 생성:
  - `docs/plans/2026-04-20-sec-filings-event-extraction.md`
  - `docs/sec-filings-event-extraction.md`
  - `docs/tasks/sec-filings-event-extraction/contract.md`
  - `docs/tasks/sec-filings-event-extraction/plan.md`
  - `docs/tasks/sec-filings-event-extraction/handoff.md`
  - `docs/tasks/sec-filings-event-extraction/review.md`
  - `scripts/verify_sec_filings_event_extract.sh`
  - `src/stockanalysis/ingest/sec/event_extract.py`
  - `tests/test_sec_event_extract.py`
- 수정:
  - `README.md`
  - `docs/verification-plan.md`
  - `docs/tasks/sec-filing-raw-fetch/handoff.md`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/sec/models.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `tests/test_ingest_cli.py`
- 의도적으로 안 건드린 것:
  - migrations and seeds
  - macro ingest code

## Decisions

- 결정:
  - event extraction 첫 단계는 deterministic heuristic path로 제한한다.
  - dedupe key는 `sec_edgar:{accession}:{event_type}` 형식으로 고정한다.
  - event link는 `source`로 기록하고 impact tables는 건드리지 않는다.
- 이유:
  - raw filing을 event 객체로 연결하는 첫 canonical path를 최소 범위로 빠르게 열기 위해서다.

## Verification Already Run

- 명령: `python3 -m compileall src tests`
- 관찰한 결과: compileall이 성공했다.

- 명령: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- 관찰한 결과: 전체 unit test 41개가 모두 통과했다.

- 명령: `bash -n /Users/woody/ai/stockanalysis/scripts/verify_sec_filings_event_extract.sh`
- 관찰한 결과: shell syntax 검사가 통과했다.

- 명령: `bash /Users/woody/ai/stockanalysis/scripts/verify_sec_filings_event_extract.sh`
- 관찰한 결과:
  - docker 기반 Postgres에 migration과 seed를 적용했다.
  - fixture 기반 `sec-filings-upsert`, `sec-filing-raw-fetch`, `sec-filings-event-extract`가 성공했다.
  - linked `event.event` row가 `1`건으로 확인됐다.
  - dedupe key `sec_edgar:0000320193-24-000123:sec_annual_report_filed` row가 `1`건으로 확인됐다.
  - latest `ops.pipeline_run` for `sec_filings_event_extract` status가 `succeeded`로 확인됐다.

- 명령: `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task sec-filings-event-extraction`
- 관찰한 결과: `Task sec-filings-event-extraction passed readiness checks.`가 출력됐다.

- 명령: `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 관찰한 결과: 출력이 없었다.

## Still Unverified

- 항목: live SEC filing body 기반 event smoke
- 왜 중요한가: 현재 검증은 fixture raw artifact 기준이라, 실제 SEC body 변형과 응답 edge case는 아직 확인하지 못했다.

- 항목: classification/instrument impact mapping
- 왜 중요한가: 현재는 event skeleton만 만들고 영향 매핑은 비어 있으므로 추천/리뷰 엔진 연결에는 후속 작업이 필요하다.

## Exact Next Step

- 다음 세션은 이것부터 시작: `sec-filings-event-batch-extract`가 완료됐으므로, `event-classification-impact-bootstrap` 또는 `sec-filings-event-retry-policy`로 확장한다.

## Risks

- 위험:
  - current extraction은 filing form type과 excerpt 기반 heuristic에 머문다.
  - classification/instrument impact mapping이 아직 없다.
  - live SEC body 구조 변화에 대한 회복력은 아직 확인하지 못했다.
- 대응:
  - 현재는 event skeleton만 먼저 만들고, richer semantics와 영향 매핑은 후속 task로 분리한다.

## Useful Context

- 파일:
  - `src/stockanalysis/ingest/sec/event_extract.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `tests/test_sec_event_extract.py`
  - `scripts/verify_sec_filings_event_extract.sh`
- 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_sec_filings_event_extract.sh`
  - `PYTHONPATH=/Users/woody/ai/stockanalysis/src python3 -m stockanalysis.ingest.cli sec-filings-event-extract --external-document-id 0000320193-24-000123`
- 다시 찾기 싫은 배경지식:
  - 현재 단계는 single SEC filing raw artifact에서 deterministic event 1건을 만드는 것까지만 구현한다.
