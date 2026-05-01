# Review Notes

이 문서는 generator와 분리된 evaluator artifact다.

코드, diff, 구조, 리스크 관점에서 변경을 검토할 때 사용한다.

## Review Scope

- 대상 task: `event-instrument-impact-bootstrap`
- 검토 대상 파일:
  - `src/stockanalysis/ingest/sec/instrument_impact.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_sec_instrument_impact.py`
  - `scripts/verify_event_instrument_impact_bootstrap.sh`
  - `docs/event-instrument-impact-bootstrap.md`
- 검토 기준: pending event discovery 정확성, company name extraction 안정성, canonical instrument lookup 보수성, pipeline_run lifecycle, integration verify 신뢰성

## Claimed Outcome

- generator가 주장하는 완료 내용: `event-instrument-impact-bootstrap` CLI가 pending SEC events를 canonical instrument와 `event.event_instrument_impact`에 연결한다.

## Evidence Checked

- 읽은 파일:
  - `src/stockanalysis/ingest/sec/instrument_impact.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_sec_instrument_impact.py`
  - `scripts/verify_event_instrument_impact_bootstrap.sh`
  - `docs/event-instrument-impact-bootstrap.md`
- 실행한 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n /Users/woody/ai/stockanalysis/scripts/verify_event_instrument_impact_bootstrap.sh`
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_event_instrument_impact_bootstrap.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task event-instrument-impact-bootstrap`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 확인한 로그 또는 산출물:
  - 전체 unit test 62개 통과
  - docker verify에서 `event.event_instrument_impact` 2건 확인
  - annual/quarterly SEC event의 `AAPL` mapping 각 1건 확인
  - latest bootstrap run status `succeeded` 확인
  - readiness 검증 통과, placeholder 미검출

## Findings

심각도 순으로 적는다.

- Finding: blocking issue 없음
- Impact: 현재 범위인 SEC event instrument impact bootstrap은 goal과 completion criteria를 충족한다.
- Evidence: fixture 기반 unit/integration 검증, `AAPL` exact-match linkage, readiness 검증이 모두 통과했다.
- Suggested fix: 없음. 다음 task에서 companyfacts ingest 또는 retry policy로 확장하면 된다.

## Residual Risks

- 아직 남아 있는 위험:
  - exact-match lookup만 지원한다.
  - multi-instrument event 확장은 아직 없다.
  - live SEC issuer alias variation에 대한 smoke가 없다.

## Open Questions

- 질문:
  - next step을 `sec-companyfacts-ingest`와 retry policy 중 어디에 둘지

## Verdict

- pass with risks
