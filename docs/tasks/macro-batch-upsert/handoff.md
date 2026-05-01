# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: macro-batch-upsert
- 담당: Codex
- 날짜: 2026-04-18

## Current Status

- 완료:
  - `macro-batch-upsert` task 문서를 생성했다.
  - batch runner와 fixture directory 전략을 구현했다.
  - `macro-batch-upsert` CLI, FEDFUNDS fixture, docker 기반 verification script, 운영 문서를 추가했다.
  - unit test, docker 기반 integration verify, task readiness 검증을 통과했다.
- 진행 중:
  - 없음.
- 막힌 점:
  - 없음.

## Files Touched

- 생성:
  - `docs/plans/2026-04-18-macro-batch-upsert.md`
  - `docs/macro-batch-upsert.md`
  - `docs/tasks/macro-batch-upsert/contract.md`
  - `docs/tasks/macro-batch-upsert/plan.md`
  - `docs/tasks/macro-batch-upsert/handoff.md`
  - `docs/tasks/macro-batch-upsert/review.md`
  - `scripts/verify_macro_batch_upsert.sh`
  - `tests/fixtures/fred_series_FEDFUNDS.json`
  - `tests/fixtures/fred_observations_FEDFUNDS.json`
- 수정:
  - `README.md`
  - `docs/verification-plan.md`
  - `docs/tasks/macro-upsert-runner/handoff.md`
  - `src/stockanalysis/ingest/macro/upsert.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_macro_upsert.py`
- 의도적으로 안 건드린 것:
  - migrations and seeds
  - single-series upsert flow

## Decisions

- 결정:
  - batch는 default series만 지원한다.
  - fixture directory는 `fred_series_<ID>.json`, `fred_observations_<ID>.json` 규칙을 사용한다.
  - series별 `pipeline_run`을 유지하고 batch summary는 별도로 만든다.
- 이유:
  - 기존 single-series runner를 재사용하기 쉽고, 검증도 단순하다.

## Verification Already Run

- 명령: `python3 -m compileall src tests`
- 관찰한 결과: compileall이 성공했다.

- 명령: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- 관찰한 결과: unit test 21개가 모두 통과했다.

- 명령: `bash -n /Users/woody/ai/stockanalysis/scripts/verify_macro_batch_upsert.sh`
- 관찰한 결과: shell syntax 검사가 통과했다.

- 명령: `bash /Users/woody/ai/stockanalysis/scripts/verify_macro_batch_upsert.sh`
- 관찰한 결과:
  - docker 기반 Postgres에 migration과 seed를 적용했다.
  - fixture 기반 `macro-batch-upsert`가 성공했다.
  - `macro.series` 2건, `macro.observation` 5건, non-null `source_run_id` 5건, succeeded `ops.pipeline_run` 2건 조건을 통과했다.

- 명령: `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task macro-batch-upsert`
- 관찰한 결과: `Task macro-batch-upsert passed readiness checks.`

- 명령: `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 관찰한 결과: 출력이 없었다.

## Still Unverified

- 항목: 실제 FRED live batch smoke
- 왜 중요한가: 현재 batch 검증은 fixture directory 기반이라, 실 API payload에서도 한 번 더 확인할 필요가 있다.

- 항목: parallel or retry orchestration
- 왜 중요한가: 현재 batch는 순차 실행이고 retry 정책이 없다.

## Exact Next Step

- 다음 세션은 이것부터 시작: `docs/tasks/macro-run-history-report/`와 `src/stockanalysis/ingest/macro/report.py`를 읽고 recent run audit 경로를 검증한다.

## Risks

- 위험:
  - batch는 여전히 순차 실행이라 느릴 수 있다.
  - partial failure 정책은 아직 고도화되지 않았다.
  - custom non-default series batch는 아직 지원하지 않는다.
- 대응:
  - 현재는 bootstrap 단계이므로 단순 순차 실행을 유지한다.
  - richer batch orchestration은 후속 task로 분리한다.

## Useful Context

- 파일:
  - `src/stockanalysis/ingest/macro/upsert.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_macro_upsert.py`
- 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_macro_batch_upsert.sh`
  - `PYTHONPATH=/Users/woody/ai/stockanalysis/src python3 -m stockanalysis.ingest.cli macro-batch-upsert --fixtures-dir tests/fixtures --series-id CPIAUCSL --series-id FEDFUNDS`
- 다시 찾기 싫은 배경지식:
  - single-series `macro-upsert`는 이미 완료되어 있고, 이번 task는 multi-series orchestration만 추가하는 단계다.
