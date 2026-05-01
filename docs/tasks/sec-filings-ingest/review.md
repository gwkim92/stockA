# Review Notes

이 문서는 generator와 분리된 evaluator artifact다.

코드, diff, 구조, 리스크 관점에서 변경을 검토할 때 사용한다.

## Review Scope

- 대상 task: `sec-filings-ingest`
- 검토 대상 파일:
  - `src/stockanalysis/ingest/sec/submissions.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `src/stockanalysis/ingest/sec/upsert.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_sec_filings.py`
  - `scripts/verify_sec_filings_ingest.sh`
  - `docs/sec-filings-ingest.md`
- 검토 기준: filing metadata mapping 정확성, source_document upsert 안정성, pipeline_run linkage, integration verify 신뢰성

## Claimed Outcome

- generator가 주장하는 완료 내용: `sec-filings-upsert` CLI가 SEC filing 메타데이터를 `ingest.source_document`에 적재하고 run history를 남긴다.

## Evidence Checked

- 읽은 파일:
  - `src/stockanalysis/ingest/sec/submissions.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `src/stockanalysis/ingest/sec/upsert.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_sec_filings.py`
  - `scripts/verify_sec_filings_ingest.sh`
  - `docs/sec-filings-ingest.md`
- 실행한 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n /Users/woody/ai/stockanalysis/scripts/verify_sec_filings_ingest.sh`
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_sec_filings_ingest.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task sec-filings-ingest`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 확인한 로그 또는 산출물:
  - 전체 unit test 30개 통과
  - docker verify에서 `source_document` 2건, non-null `ingested_by_run_id` 2건 확인
  - latest `sec_filings_upsert` pipeline run status `succeeded` 확인
  - readiness 검증 통과, placeholder 미검출

## Findings

심각도 순으로 적는다.

- Finding: blocking issue 없음
- Impact: 현재 범위인 SEC filings metadata ingest는 goal과 completion criteria를 충족한다.
- Evidence: fixture 기반 unit/integration 검증과 canonical DB write 확인이 모두 통과했다.
- Suggested fix: 없음. 다음 task에서 live SEC smoke와 raw filing artifact 저장 경로를 분리해 추가하면 된다.

## Residual Risks

- 아직 남아 있는 위험:
  - 현재 ingest는 metadata only라 filing body 기반 event extraction은 바로 할 수 없다.
  - issuer/instrument mapping이 없어 filing metadata가 아직 종목 엔터티와 직접 연결되지는 않는다.
  - integration verify는 fixture 기반이므로 live SEC rate limit, headers, 응답 변형은 별도 smoke가 필요하다.

## Open Questions

- 질문:
  - 원문 저장을 `raw_storage_uri` 중심으로 갈지, 별도 raw artifact table을 둘지
  - SEC 확장의 다음 우선순위를 `raw filing fetch`와 `companyfacts ingest` 중 어디에 둘지

## Verdict

- pass
- pass with risks
