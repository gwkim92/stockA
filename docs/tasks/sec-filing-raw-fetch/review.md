# Review Notes

이 문서는 generator와 분리된 evaluator artifact다.

코드, diff, 구조, 리스크 관점에서 변경을 검토할 때 사용한다.

## Review Scope

- 대상 task: `sec-filing-raw-fetch`
- 검토 대상 파일:
  - `src/stockanalysis/ingest/sec/raw_fetch.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_sec_raw_fetch.py`
  - `scripts/verify_sec_filing_raw_fetch.sh`
  - `docs/sec-filing-raw-fetch.md`
- 검토 기준: source_document lookup 정확성, raw artifact write 안정성, checksum update 정확성, pipeline_run lifecycle, integration verify 신뢰성

## Claimed Outcome

- generator가 주장하는 완료 내용: `sec-filing-raw-fetch` CLI가 SEC filing body를 artifact로 저장하고 `raw_storage_uri`, `checksum`을 `ingest.source_document`에 반영한다.

## Evidence Checked

- 읽은 파일:
  - `src/stockanalysis/ingest/sec/raw_fetch.py`
  - `src/stockanalysis/ingest/sec/sql.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_sec_raw_fetch.py`
  - `scripts/verify_sec_filing_raw_fetch.sh`
  - `docs/sec-filing-raw-fetch.md`
- 실행한 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n /Users/woody/ai/stockanalysis/scripts/verify_sec_filing_raw_fetch.sh`
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_sec_filing_raw_fetch.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task sec-filing-raw-fetch`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 확인한 로그 또는 산출물:
  - 전체 unit test 35개 통과
  - docker verify에서 `raw_storage_uri like 'file://%'` and non-null `checksum` row 1건 확인
  - latest `sec_filing_raw_fetch` pipeline run status `succeeded` 확인
  - artifact file 1건 생성 확인
  - readiness 검증 통과, placeholder 미검출

## Findings

심각도 순으로 적는다.

- Finding: blocking issue 없음
- Impact: 현재 범위인 single-document SEC raw fetch는 goal과 completion criteria를 충족한다.
- Evidence: fixture 기반 unit/integration 검증과 canonical DB update, artifact file 생성 확인이 모두 통과했다.
- Suggested fix: 없음. 다음 task에서 batch raw fetch 또는 raw artifact 기반 event extraction으로 확장하면 된다.

## Residual Risks

- 아직 남아 있는 위험:
  - raw fetch lineage가 별도 artifact table 없이 `source_document` row update에 머문다.
  - local file URI 저장 전략은 장기 공유 런타임이나 object storage와 직접 맞지 않을 수 있다.
  - integration verify는 fixture body 기준이라 live SEC fetch edge case는 별도 smoke가 필요하다.

## Open Questions

- 질문:
  - raw artifact 저장소를 계속 local file URI로 둘지 object storage URI로 일반화할지
  - 다음 우선순위를 `sec-filings-event-extraction`과 `sec-filing-raw-batch-fetch` 중 어디에 둘지

## Verdict

- pass with risks
