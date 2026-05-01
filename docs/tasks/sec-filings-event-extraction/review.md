# Review Notes

이 문서는 generator와 분리된 evaluator artifact다.

코드, diff, 구조, 리스크 관점에서 변경을 검토할 때 사용한다.

## Review Scope

- 대상 task: `sec-filings-event-extraction`
- 검토 대상 파일:
  - `src/stockanalysis/ingest/sec/event_extract.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_sec_event_extract.py`
  - `scripts/verify_sec_filings_event_extract.sh`
  - `docs/sec-filings-event-extraction.md`
- 검토 기준: heuristic mapping 정확성, event dedupe 안정성, source document linkage, pipeline_run lifecycle, integration verify 신뢰성

## Claimed Outcome

- generator가 주장하는 완료 내용: `sec-filings-event-extract` CLI가 raw SEC filing artifact에서 event row를 만들고 source document link를 남긴다.

## Evidence Checked

- 읽은 파일:
  - `src/stockanalysis/ingest/sec/event_extract.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_sec_event_extract.py`
  - `scripts/verify_sec_filings_event_extract.sh`
  - `docs/sec-filings-event-extraction.md`
- 실행한 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n /Users/woody/ai/stockanalysis/scripts/verify_sec_filings_event_extract.sh`
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_sec_filings_event_extract.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task sec-filings-event-extraction`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 확인한 로그 또는 산출물:
  - 전체 unit test 41개 통과
  - docker verify에서 linked `event.event` 1건과 dedupe key 1건 확인
  - latest `sec_filings_event_extract` pipeline run status `succeeded` 확인
  - readiness 검증 통과, placeholder 미검출

## Findings

심각도 순으로 적는다.

- Finding: blocking issue 없음
- Impact: 현재 범위인 single-document SEC event extraction은 goal과 completion criteria를 충족한다.
- Evidence: fixture 기반 unit/integration 검증과 canonical event row, source link, dedupe key 확인이 모두 통과했다.
- Suggested fix: 없음. 다음 task에서 batch extraction 또는 impact mapping으로 확장하면 된다.

## Residual Risks

- 아직 남아 있는 위험:
  - heuristic mapping이 form type 중심이라 semantic nuance는 반영하지 못한다.
  - event impact tables는 아직 비어 있다.
  - integration verify는 fixture raw artifact 기준이라 live SEC body 변형에 대한 추가 smoke가 필요하다.

## Open Questions

- 질문:
  - 다음 우선순위를 batch extraction과 classification impact bootstrap 중 어디에 둘지
  - semantic enrichment를 separate LLM pipeline으로 둘지, 기존 extraction path를 확장할지

## Verdict

- pass with risks
