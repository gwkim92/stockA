# Review Notes

이 문서는 generator와 분리된 evaluator artifact다.

코드, diff, 구조, 리스크 관점에서 변경을 검토할 때 사용한다.

## Review Scope

- 대상 task: `macro-batch-upsert`
- 검토 대상 파일:
  - `src/stockanalysis/ingest/macro/upsert.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_macro_upsert.py`
  - `scripts/verify_macro_batch_upsert.sh`
  - `docs/macro-batch-upsert.md`
- 검토 기준: multi-series summary 일관성, fixture directory contract, single-series runner 재사용, integration verify 신뢰성

## Claimed Outcome

- generator가 주장하는 완료 내용: `macro-batch-upsert` CLI가 여러 기본 macro series를 순차 적재하고, batch summary와 per-series 결과를 반환한다.

## Evidence Checked

- 읽은 파일:
  - `src/stockanalysis/ingest/macro/upsert.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_macro_upsert.py`
  - `scripts/verify_macro_batch_upsert.sh`
  - `docs/macro-batch-upsert.md`
- 실행한 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n /Users/woody/ai/stockanalysis/scripts/verify_macro_batch_upsert.sh`
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_macro_batch_upsert.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task macro-batch-upsert`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 확인한 로그 또는 산출물:
  - unit test 21개 통과 로그
  - docker 기반 2-series batch upsert verify 성공
  - placeholder 검색 빈 결과

## Findings

심각도 순으로 적는다.

- Finding: blocking finding 없음
- Impact: 현재 범위의 multi-series batch execute와 per-series pipeline_run 보존은 검증 기준을 충족한다.
- Evidence: `tests/test_macro_upsert.py`, `scripts/verify_macro_batch_upsert.sh`, readiness 검증
- Suggested fix: 없음

- Finding: batch는 순차 실행이며 retry/parallel 정책이 없다.
- Impact: series 수가 늘어나면 실행 시간이 길고 운영 편의성이 제한된다.
- Evidence: `src/stockanalysis/ingest/macro/upsert.py`의 순차 loop와 `docs/macro-batch-upsert.md`의 current limits
- Suggested fix: `macro-batch-retry-policy`와 `parallel batch` 검토 task를 분리한다.

## Residual Risks

- 아직 남아 있는 위험:
  - live FRED payload 기반 batch smoke는 아직 미검증이다.
  - custom non-default series batch는 지원하지 않는다.

## Open Questions

- 질문:
  - batch run에 상위 batch_run 엔터티를 추가할지, 현재처럼 series별 run만 유지할지

## Verdict

- pass with risks
