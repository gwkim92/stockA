# Review Notes

이 문서는 generator와 분리된 evaluator artifact다.

코드, diff, 구조, 리스크 관점에서 변경을 검토할 때 사용한다.

## Review Scope

- 대상 task: `sec-companyfacts-ingest`
- 검토 대상 파일:
  - `src/stockanalysis/ingest/sec/companyfacts.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_sec_companyfacts.py`
  - `scripts/verify_sec_companyfacts_ingest.sh`
  - `docs/sec-companyfacts-ingest.md`
- 검토 기준: metric filtering 정확성, period/value mapping, canonical instrument lookup 보수성, pipeline_run lifecycle, integration verify 신뢰성

## Claimed Outcome

- generator가 주장하는 완료 내용: `sec-companyfacts-upsert` CLI가 selected SEC companyfacts facts를 canonical financial tables에 적재한다.

## Evidence Checked

- 읽은 파일:
  - `src/stockanalysis/ingest/sec/companyfacts.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_sec_companyfacts.py`
  - `scripts/verify_sec_companyfacts_ingest.sh`
  - `docs/sec-companyfacts-ingest.md`
- 실행한 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n /Users/woody/ai/stockanalysis/scripts/verify_sec_companyfacts_ingest.sh`
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_sec_companyfacts_ingest.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task sec-companyfacts-ingest`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 확인한 로그 또는 산출물:
  - 전체 unit test 68개 통과
  - docker verify에서 period row 2건, metric row 4건 확인
  - non-null `source_document_id` 2건, annual revenue 1건, quarterly net income 1건 확인
  - latest bootstrap run status `succeeded` 확인
  - readiness 검증 통과, placeholder 미검출

## Findings

심각도 순으로 적는다.

- Finding: blocking issue 없음
- Impact: 현재 범위인 SEC companyfacts ingest는 goal과 completion criteria를 충족한다.
- Evidence: fixture 기반 unit/integration 검증, canonical period/value linkage, readiness 검증이 모두 통과했다.
- Suggested fix: 없음. 다음 task에서 market price ingest 또는 richer concept coverage로 확장하면 된다.

## Residual Risks

- 아직 남아 있는 위험:
  - selected metric subset만 지원한다.
  - instant facts와 IFRS facts는 아직 비어 있다.
  - live companyfacts smoke가 없다.

## Open Questions

- 질문:
  - next step을 market price ingest와 retry policy 중 어디에 둘지

## Verdict

- pass with risks
