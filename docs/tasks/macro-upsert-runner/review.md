# Review Notes

이 문서는 generator와 분리된 evaluator artifact다.

코드, diff, 구조, 리스크 관점에서 변경을 검토할 때 사용한다.

## Review Scope

- 대상 task: `macro-upsert-runner`
- 검토 대상 파일:
  - `src/stockanalysis/ingest/config.py`
  - `src/stockanalysis/ingest/psql.py`
  - `src/stockanalysis/ingest/macro/sql.py`
  - `src/stockanalysis/ingest/macro/upsert.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_macro_upsert.py`
  - `scripts/verify_macro_upsert_runner.sh`
  - `docs/macro-upsert-runner.md`
- 검토 기준: pipeline run lifecycle 보존, canonical DB write 가능성, fixture 기반 검증 가능성, 다음 batch task로의 확장성

## Claimed Outcome

- generator가 주장하는 완료 내용: `macro-upsert` CLI가 fixture 기반 macro payload를 canonical Postgres에 적재하고 `ops.pipeline_run`에 실행 이력을 남긴다.

## Evidence Checked

- 읽은 파일:
  - `src/stockanalysis/ingest/config.py`
  - `src/stockanalysis/ingest/psql.py`
  - `src/stockanalysis/ingest/macro/sql.py`
  - `src/stockanalysis/ingest/macro/upsert.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_macro_upsert.py`
  - `scripts/verify_macro_upsert_runner.sh`
  - `docs/macro-upsert-runner.md`
- 실행한 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n /Users/woody/ai/stockanalysis/scripts/verify_macro_upsert_runner.sh`
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_macro_upsert_runner.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task macro-upsert-runner`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 확인한 로그 또는 산출물:
  - unit test 17개 통과 로그
  - docker 기반 macro upsert verify 성공
  - latest `ops.pipeline_run.status='succeeded'` 확인
  - placeholder 검색 빈 결과

## Findings

심각도 순으로 적는다.

- Finding: blocking finding 없음
- Impact: 현재 범위의 single-series canonical write와 pipeline_run linkage는 검증 기준을 충족한다.
- Evidence: `tests/test_macro_upsert.py`, `scripts/verify_macro_upsert_runner.sh`, readiness 검증
- Suggested fix: 없음

- Finding: `psql` command path와 single-series granularity는 장기 확장성 제약이 있다.
- Impact: batch orchestration과 richer connection control은 후속 task가 필요하다.
- Evidence: `docs/macro-upsert-runner.md`의 current limits와 `src/stockanalysis/ingest/macro/upsert.py`의 단일 series runner 구조
- Suggested fix: `macro-batch-upsert`와 Python driver 재평가 task를 분리한다.

## Residual Risks

- 아직 남아 있는 위험:
  - live FRED payload 기반 smoke는 아직 미검증이다.
  - `psql` subprocess path는 장기 운영 시 observability와 retry 제어가 제한된다.

## Open Questions

- 질문:
  - batch run 단위를 series별 run으로 유지할지, batch 1건으로 묶을지

## Verdict

- pass with risks
