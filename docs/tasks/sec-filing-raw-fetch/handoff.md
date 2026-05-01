# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: sec-filing-raw-fetch
- 담당: Codex
- 날짜: 2026-04-20

## Current Status

- 완료:
  - `sec-filing-raw-fetch` task 문서를 생성했다.
  - `source_document` lookup, raw artifact write, checksum update 로직을 구현했다.
  - `sec-filing-raw-fetch` CLI와 fixture 기반 integration verify script를 추가했다.
  - unit test, docker 기반 integration verify, readiness 검증을 통과했다.
- 진행 중:
  - 없음.
- 막힌 점:
  - 없음.

## Files Touched

- 생성:
  - `docs/plans/2026-04-20-sec-filing-raw-fetch.md`
  - `docs/sec-filing-raw-fetch.md`
  - `docs/tasks/sec-filing-raw-fetch/contract.md`
  - `docs/tasks/sec-filing-raw-fetch/plan.md`
  - `docs/tasks/sec-filing-raw-fetch/handoff.md`
  - `docs/tasks/sec-filing-raw-fetch/review.md`
  - `scripts/verify_sec_filing_raw_fetch.sh`
  - `src/stockanalysis/ingest/sec/raw_fetch.py`
  - `tests/test_sec_raw_fetch.py`
  - `tests/fixtures/sec_filing_aapl_20240928_10k.html`
- 수정:
  - `README.md`
  - `docs/verification-plan.md`
  - `docs/tasks/sec-filings-ingest/handoff.md`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/sec/models.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `tests/test_ingest_cli.py`
- 의도적으로 안 건드린 것:
  - migrations and seeds
  - macro ingest code

## Decisions

- 결정:
  - raw artifact는 기존 `source_document` row의 `raw_storage_uri`, `checksum`으로 먼저 연결한다.
  - metadata ingest lineage 보존을 위해 기존 `ingested_by_run_id`는 덮어쓰지 않는다.
  - deterministic 검증은 fixture HTML body로 고정한다.
- 이유:
  - 새 테이블을 만들지 않고도 event extraction 이전 단계까지 빠르게 연결할 수 있기 때문이다.

## Verification Already Run

- 명령: `python3 -m compileall src tests`
- 관찰한 결과: compileall이 성공했다.

- 명령: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- 관찰한 결과: 전체 unit test 35개가 모두 통과했다.

- 명령: `bash -n /Users/woody/ai/stockanalysis/scripts/verify_sec_filing_raw_fetch.sh`
- 관찰한 결과: shell syntax 검사가 통과했다.

- 명령: `bash /Users/woody/ai/stockanalysis/scripts/verify_sec_filing_raw_fetch.sh`
- 관찰한 결과:
  - docker 기반 Postgres에 migration과 seed를 적용했다.
  - fixture 기반 `sec-filings-upsert`와 `sec-filing-raw-fetch`가 성공했다.
  - `raw_storage_uri like 'file://%'` and non-null `checksum` row가 `1`건으로 확인됐다.
  - latest `ops.pipeline_run` for `sec_filing_raw_fetch` status가 `succeeded`로 확인됐다.
  - artifact root 아래 file count가 `1`건으로 확인됐다.

- 명령: `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task sec-filing-raw-fetch`
- 관찰한 결과: `Task sec-filing-raw-fetch passed readiness checks.`가 출력됐다.

- 명령: `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 관찰한 결과: 출력이 없었다.

## Still Unverified

- 항목: live SEC document fetch smoke
- 왜 중요한가: 현재 raw fetch 검증은 fixture body 기준이라, 실제 SEC headers와 응답 변형까지는 확인하지 못했다.

- 항목: multi-document pending queue 처리
- 왜 중요한가: 현재는 single accession 단위 CLI만 있어 대량 공시 백필에는 추가 batch orchestration이 필요하다.

## Exact Next Step

- 다음 세션은 이것부터 시작: `sec-filings-event-extraction`가 완료됐으므로, batch extraction 또는 event impact 매핑으로 확장한다.

## Risks

- 위험:
  - raw fetch lineage가 아직 `source_document` row update에 머문다.
  - live SEC fetch는 아직 fixture 검증 밖에 없다.
  - local file URI 저장 방식은 장기적으로 object storage나 shared runtime에 그대로 맞지 않을 수 있다.
- 대응:
  - 현재는 single-document raw path를 먼저 고정하고, richer lineage와 live smoke는 후속 task로 분리한다.

## Useful Context

- 파일:
  - `src/stockanalysis/ingest/sec/raw_fetch.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `tests/test_sec_raw_fetch.py`
  - `scripts/verify_sec_filing_raw_fetch.sh`
- 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_sec_filing_raw_fetch.sh`
  - `PYTHONPATH=/Users/woody/ai/stockanalysis/src python3 -m stockanalysis.ingest.cli sec-filing-raw-fetch --external-document-id 0000320193-24-000123 --body-file tests/fixtures/sec_filing_aapl_20240928_10k.html`
- 다시 찾기 싫은 배경지식:
  - 현재 단계는 raw filing artifact 1건을 deterministic하게 저장하고 canonical row에 checksum을 연결하는 것까지만 구현한다.
