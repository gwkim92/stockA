# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: sec-companyfacts-ingest
- 담당: Codex
- 날짜: 2026-04-20

## Current Status

- 완료:
  - `sec-companyfacts-ingest` task 문서를 생성했다.
  - companyfacts parser, SQL, CLI, 테스트, verify script를 구현했다.
  - unit test, docker 기반 integration verify, readiness 검증을 통과했다.
- 진행 중:
  - 없음.
- 막힌 점:
  - 없음.

## Files Touched

- 생성:
  - `docs/plans/2026-04-20-sec-companyfacts-ingest.md`
  - `docs/sec-companyfacts-ingest.md`
  - `docs/tasks/sec-companyfacts-ingest/contract.md`
  - `docs/tasks/sec-companyfacts-ingest/plan.md`
  - `docs/tasks/sec-companyfacts-ingest/handoff.md`
  - `docs/tasks/sec-companyfacts-ingest/review.md`
  - `scripts/verify_sec_companyfacts_ingest.sh`
  - `src/stockanalysis/ingest/sec/companyfacts.py`
  - `tests/fixtures/sec_companyfacts_CIK0000320193.json`
  - `tests/test_sec_companyfacts.py`
- 수정:
  - `README.md`
  - `docs/tasks/event-instrument-impact-bootstrap/handoff.md`
  - `docs/verification-plan.md`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/sec/models.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `tests/test_ingest_cli.py`
- 의도적으로 안 건드린 것:
  - migrations and seeds
  - macro ingest code

## Decisions

- 결정:
  - first-step ingest는 selected `us-gaap` USD duration metrics만 사용한다.
  - canonical instrument linkage는 exact-match lookup만 허용한다.
  - source document linkage는 accession number가 있을 때만 optional로 연결한다.
- 이유:
  - period semantics와 instrument resolution을 보수적으로 유지하면서 deterministic financial ingest path를 먼저 열기 위해서다.

## Verification Already Run

- 명령: `python3 -m compileall src tests`
- 관찰한 결과: compileall이 성공했다.

- 명령: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- 관찰한 결과: 전체 unit test 68개가 모두 통과했다.

- 명령: `bash -n /Users/woody/ai/stockanalysis/scripts/verify_sec_companyfacts_ingest.sh`
- 관찰한 결과: shell syntax 검사가 통과했다.

- 명령: `bash /Users/woody/ai/stockanalysis/scripts/verify_sec_companyfacts_ingest.sh`
- 관찰한 결과:
  - docker 기반 Postgres에 migration과 seed를 적용했다.
  - fixture 기반 `sec-filings-upsert`와 canonical Apple issuer/instrument insert가 성공했다.
  - fixture 기반 `sec-companyfacts-upsert`가 성공했다.
  - `market.financial_statement_period` 2건과 `market.financial_metric_value` 4건이 생성됐다.
  - non-null `source_document_id` 2건, annual revenue 1건, quarterly net income 1건이 확인됐다.
  - latest `sec_companyfacts_upsert` pipeline run status가 `succeeded`로 확인됐다.

- 명령: `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task sec-companyfacts-ingest`
- 관찰한 결과: `Task sec-companyfacts-ingest passed readiness checks.`가 출력됐다.

- 명령: `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 관찰한 결과: 출력이 없었다.

## Still Unverified

- 항목: live companyfacts smoke
- 왜 중요한가: 현재 검증은 fixture 기반 Apple payload만 확인하므로, 실제 개별 issuer variation과 larger concept coverage는 별도 확인이 필요하다.

- 항목: instant fact coverage
- 왜 중요한가: balance sheet 계열 instant facts는 아직 canonical schema에 넣지 않는다.

## Exact Next Step

- 다음 세션은 이것부터 시작: `market-price-ingest`가 열렸으므로, 다음은 `market-price-batch-ingest` 또는 `sec-filings-event-retry-policy`로 확장한다.

## Risks

- 위험:
  - selected metric subset만 지원한다.
  - exact-match instrument lookup만 지원한다.
  - instant facts와 IFRS facts는 아직 비어 있다.
- 대응:
  - 현재는 deterministic financial ingest만 먼저 고정하고 richer concept coverage와 broader resolution은 후속 task로 분리한다.

## Useful Context

- 파일:
  - `src/stockanalysis/ingest/sec/companyfacts.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `tests/test_sec_companyfacts.py`
  - `scripts/verify_sec_companyfacts_ingest.sh`
- 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_sec_companyfacts_ingest.sh`
  - `PYTHONPATH=/Users/woody/ai/stockanalysis/src python3 -m stockanalysis.ingest.cli sec-companyfacts-upsert --cik 320193`
- 다시 찾기 싫은 배경지식:
  - 현재 단계는 Apple fixture 기준 annual/quarterly duration metrics 4건을 canonical financial tables로 적재하는 것까지만 구현한다.
