# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: sec-filings-ingest
- 담당: Codex
- 날짜: 2026-04-18

## Current Status

- 완료:
  - `sec-filings-ingest` task 문서를 생성했다.
  - SEC submissions recent filings payload 정규화 코드를 구현했다.
  - filing metadata -> `ingest.source_document` upsert SQL renderer를 구현했다.
  - `sec-filings-sync`, `sec-filings-upsert` CLI를 추가했다.
  - `ops.pipeline_run` 생성/성공/실패 갱신이 포함된 canonical write runner를 구현했다.
  - fixture 기반 unit test, docker 기반 integration verify, readiness 검증을 통과했다.
- 진행 중:
  - 없음.
- 막힌 점:
  - 없음.

## Files Touched

- 생성:
  - `docs/plans/2026-04-18-sec-filings-ingest.md`
  - `docs/sec-filings-ingest.md`
  - `docs/tasks/sec-filings-ingest/contract.md`
  - `docs/tasks/sec-filings-ingest/plan.md`
  - `docs/tasks/sec-filings-ingest/handoff.md`
  - `docs/tasks/sec-filings-ingest/review.md`
  - `scripts/verify_sec_filings_ingest.sh`
  - `src/stockanalysis/ingest/sec/__init__.py`
  - `src/stockanalysis/ingest/sec/models.py`
  - `src/stockanalysis/ingest/sec/submissions.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `src/stockanalysis/ingest/sec/upsert.py`
  - `tests/fixtures/sec_submissions_CIK0000320193.json`
  - `tests/test_sec_filings.py`
- 수정:
  - `README.md`
  - `docs/verification-plan.md`
  - `docs/tasks/macro-run-history-report/handoff.md`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_ingest_cli.py`
- 의도적으로 안 건드린 것:
  - migrations and seeds
  - macro ingest code

## Decisions

- 결정:
  - 현재 SEC ingest는 metadata only로 유지한다.
  - archive URL은 SEC archive 규칙으로 생성한다.
  - filings는 `source_document.document_type='filing'`으로 저장한다.
- 이유:
  - source_document가 이후 event extraction의 첫 연결점이기 때문이다.

## Verification Already Run

- 명령: `python3 -m compileall src tests`
- 관찰한 결과: compileall이 성공했다.

- 명령: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- 관찰한 결과: 전체 unit test 30개가 모두 통과했다.

- 명령: `bash -n /Users/woody/ai/stockanalysis/scripts/verify_sec_filings_ingest.sh`
- 관찰한 결과: shell syntax 검사가 통과했다.

- 명령: `bash /Users/woody/ai/stockanalysis/scripts/verify_sec_filings_ingest.sh`
- 관찰한 결과:
  - docker 기반 Postgres에 migration과 seed를 적용했다.
  - fixture 기반 `sec-filings-upsert`가 성공했다.
  - `ingest.source_document`에서 `sec_edgar` 기준 row count가 `2`로 확인됐다.
  - non-null `ingested_by_run_id`가 `2`건으로 확인됐다.
  - latest `ops.pipeline_run` for `sec_filings_upsert` status가 `succeeded`로 확인됐다.

- 명령: `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task sec-filings-ingest`
- 관찰한 결과: `Task sec-filings-ingest passed readiness checks.`가 출력됐다.

- 명령: `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 관찰한 결과: 출력이 없었다.

## Still Unverified

- 항목: live SEC submissions payload smoke
- 왜 중요한가: 현재 canonical write 검증은 fixture 기준이므로, 실제 rate limit/user-agent 환경에서도 같은 normalize path가 문제없는지 확인할 필요가 있다.

- 항목: filing body/raw artifact 저장
- 왜 중요한가: 현재는 metadata only라 이후 event extraction을 하려면 원문 fetch/storage 계층이 추가로 필요하다.

## Exact Next Step

- 다음 세션은 이것부터 시작: `sec-filing-raw-fetch`가 완료됐으므로, raw artifact를 이용한 `sec-filings-event-extraction` 또는 이후 `sec-companyfacts-ingest`로 확장한다.

## Risks

- 위험:
  - filing body/raw artifact는 아직 저장하지 않는다.
  - issuer/instrument mapping이 아직 없다.
  - fixture 중심 검증이라 live SEC 응답의 user-agent/rate-limit edge case는 아직 보지 못했다.
- 대응:
  - 현재는 metadata-only로 빠르게 경로를 연다.

## Useful Context

- 파일:
  - `src/stockanalysis/ingest/sec/submissions.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `src/stockanalysis/ingest/sec/upsert.py`
  - `tests/test_sec_filings.py`
- 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_sec_filings_ingest.sh`
  - `PYTHONPATH=/Users/woody/ai/stockanalysis/src python3 -m stockanalysis.ingest.cli sec-filings-upsert --cik 320193 --submissions-json tests/fixtures/sec_submissions_CIK0000320193.json`
- 다시 찾기 싫은 배경지식:
  - 현재 단계는 `source_document` metadata ingest까지만 구현한다.
