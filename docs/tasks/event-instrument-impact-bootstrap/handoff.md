# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: event-instrument-impact-bootstrap
- 담당: Codex
- 날짜: 2026-04-20

## Current Status

- 완료:
  - `event-instrument-impact-bootstrap` task 문서를 생성했다.
  - instrument impact bootstrap 코드, CLI, 테스트, verify script를 구현했다.
  - pending SEC event -> canonical instrument exact-match linkage 경로를 추가했다.
-  - unit test, docker 기반 integration verify, readiness 검증을 통과했다.
- 진행 중:
  - 없음.
- 막힌 점:
  - 없음.

## Files Touched

- 생성:
  - `docs/event-instrument-impact-bootstrap.md`
  - `docs/tasks/event-instrument-impact-bootstrap/contract.md`
  - `docs/tasks/event-instrument-impact-bootstrap/plan.md`
  - `docs/tasks/event-instrument-impact-bootstrap/handoff.md`
  - `docs/tasks/event-instrument-impact-bootstrap/review.md`
  - `scripts/verify_event_instrument_impact_bootstrap.sh`
  - `src/stockanalysis/ingest/sec/instrument_impact.py`
  - `tests/test_sec_instrument_impact.py`
- 수정:
  - `README.md`
  - `docs/plans/2026-04-20-event-instrument-impact-bootstrap.md`
  - `docs/tasks/event-classification-impact-bootstrap/handoff.md`
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
  - bootstrap은 exact-match canonical instrument lookup만 허용한다.
  - company name은 event title 우선, summary 보조 규칙으로 추출한다.
  - unresolved event가 있어도 batch 전체는 계속 진행하고 per-event failure를 summary에 남긴다.
- 이유:
  - 잘못된 종목 연결 리스크를 줄이면서 deterministic bootstrap path를 먼저 열기 위해서다.

## Verification Already Run

- 명령: `python3 -m compileall src tests`
- 관찰한 결과: compileall이 성공했다.

- 명령: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- 관찰한 결과: 전체 unit test 62개가 모두 통과했다.

- 명령: `bash -n /Users/woody/ai/stockanalysis/scripts/verify_event_instrument_impact_bootstrap.sh`
- 관찰한 결과: shell syntax 검사가 통과했다.

- 명령: `bash /Users/woody/ai/stockanalysis/scripts/verify_event_instrument_impact_bootstrap.sh`
- 관찰한 결과:
  - docker 기반 Postgres에 migration과 seed를 적용했다.
  - fixture 기반 `sec-filings-upsert`, 2건 `sec-filing-raw-fetch`, `sec-filings-event-batch-extract`가 성공했다.
  - canonical Apple issuer/instrument insert가 성공했다.
  - `event.event_instrument_impact` 2건이 생성됐다.
  - annual/quarterly SEC event가 각각 `AAPL`에 1건씩 연결된 것이 확인됐다.
  - latest `event_instrument_impact_bootstrap` pipeline run status가 `succeeded`로 확인됐다.

- 명령: `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task event-instrument-impact-bootstrap`
- 관찰한 결과: `Task event-instrument-impact-bootstrap passed readiness checks.`가 출력됐다.

- 명령: `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 관찰한 결과: 출력이 없었다.

## Still Unverified

- 항목: live SEC issuer/instrument smoke
- 왜 중요한가: 현재 검증은 fixture 기반 Apple exact-match만 확인하므로, 실제 issuer alias variation은 별도 확인이 필요하다.

- 항목: fuzzy alias resolution
- 왜 중요한가: current bootstrap은 exact-match만 지원하므로 real-world issuer name variation을 아직 흡수하지 못한다.

## Exact Next Step

- 다음 세션은 이것부터 시작: `sec-companyfacts-ingest`가 열렸으므로, 다음은 `market-price-ingest` 또는 `sec-filings-event-retry-policy`로 확장한다.

## Risks

- 위험:
  - exact-match lookup만 지원한다.
  - issuer/instrument master가 비어 있으면 event linkage도 비어 있게 된다.
  - live SEC issuer naming variation에 대한 smoke는 아직 없다.
- 대응:
  - 현재는 deterministic bootstrap만 고정하고 richer symbol resolution은 후속 task로 분리한다.

## Useful Context

- 파일:
  - `src/stockanalysis/ingest/sec/instrument_impact.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `tests/test_sec_instrument_impact.py`
  - `scripts/verify_event_instrument_impact_bootstrap.sh`
- 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_event_instrument_impact_bootstrap.sh`
  - `PYTHONPATH=/Users/woody/ai/stockanalysis/src python3 -m stockanalysis.ingest.cli event-instrument-impact-bootstrap --limit 20`
- 다시 찾기 싫은 배경지식:
  - 현재 단계는 SEC reporting event를 canonical instrument 한 종목에 deterministic하게 연결하는 것까지만 구현한다.
