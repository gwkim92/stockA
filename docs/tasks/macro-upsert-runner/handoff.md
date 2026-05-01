# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: macro-upsert-runner
- 담당: Codex
- 날짜: 2026-04-18

## Current Status

- 완료:
  - `macro-upsert-runner` task를 scaffold 대신 수동으로 생성했다.
  - `psql` 명령 기반 실행기와 `macro-upsert` runner를 추가했다.
  - `macro-upsert` CLI, unit test, integration verify script, 운영 문서를 추가했다.
  - unit test, docker 기반 integration verify, task readiness 검증을 통과했다.
- 진행 중:
  - 없음.
- 막힌 점:
  - 없음.

## Files Touched

- 생성:
  - `docs/plans/2026-04-18-macro-upsert-runner.md`
  - `docs/macro-upsert-runner.md`
  - `docs/tasks/macro-upsert-runner/contract.md`
  - `docs/tasks/macro-upsert-runner/plan.md`
  - `docs/tasks/macro-upsert-runner/handoff.md`
  - `docs/tasks/macro-upsert-runner/review.md`
  - `src/stockanalysis/ingest/psql.py`
  - `src/stockanalysis/ingest/macro/upsert.py`
  - `scripts/verify_macro_upsert_runner.sh`
  - `tests/test_macro_upsert.py`
- 수정:
  - `.env.example`
  - `README.md`
  - `docs/verification-plan.md`
  - `src/stockanalysis/ingest/config.py`
  - `src/stockanalysis/ingest/macro/sql.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_ingest_cli.py`
- 의도적으로 안 건드린 것:
  - migrations and seeds
  - `macro-ingest` fixture payload

## Decisions

- 결정:
  - direct execute는 새 dependency 없이 `psql` command wrapper로 구현한다.
  - `macro-upsert`는 series 단위 pipeline run 한 건을 생성한다.
  - failure 시에도 가능한 범위에서 `ops.pipeline_run.status='failed'`를 남긴다.
- 이유:
  - stdlib만으로 실행 경로를 열 수 있고, docker 기반 검증과 잘 맞는다.
  - 현재 범위는 batch orchestration보다 single-series canonical write가 우선이다.

## Verification Already Run

- 명령: `python3 -m compileall src tests`
- 관찰한 결과: compileall이 성공했다.

- 명령: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- 관찰한 결과: unit test 17개가 모두 통과했다.

- 명령: `bash -n /Users/woody/ai/stockanalysis/scripts/verify_macro_upsert_runner.sh`
- 관찰한 결과: shell syntax 검사가 통과했다.

- 명령: `bash /Users/woody/ai/stockanalysis/scripts/verify_macro_upsert_runner.sh`
- 관찰한 결과:
  - docker 기반 Postgres에 migration과 seed를 적용했다.
  - fixture 기반 `macro-upsert`가 성공했다.
  - `macro.series` 1건, `macro.observation` 2건, non-null `source_run_id` 2건, latest `ops.pipeline_run.status='succeeded'` 조건을 통과했다.

- 명령: `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task macro-upsert-runner`
- 관찰한 결과: `Task macro-upsert-runner passed readiness checks.`

- 명령: `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 관찰한 결과: 출력이 없었다.

## Still Unverified

- 항목: 실제 FRED live fetch smoke
- 왜 중요한가: 현재 canonical write 검증은 fixture 기반이라, 실 API payload로도 한 번 더 확인할 필요가 있다.

- 항목: multi-series batch execute
- 왜 중요한가: 현재는 single-series run만 지원한다.

## Exact Next Step

- 다음 세션은 이것부터 시작: `docs/tasks/macro-batch-upsert/`와 `src/stockanalysis/ingest/macro/upsert.py`를 읽고 multi-series batch execute를 검증한다.

## Risks

- 위험:
  - `psql` command path는 장기적으로 Python driver보다 제약이 많다.
  - current runner는 live API fetch smoke를 포함하지 않는다.
  - 현재 run granularity는 series 1개당 1건이라 batch orchestration이 없다.
- 대응:
  - 현재는 bootstrap 단계이므로 단순한 경로를 우선 채택한다.
  - live fetch와 batch orchestration은 다음 task로 분리한다.

## Useful Context

- 파일:
  - `src/stockanalysis/ingest/psql.py`
  - `src/stockanalysis/ingest/macro/upsert.py`
  - `src/stockanalysis/ingest/macro/sql.py`
  - `docs/macro-upsert-runner.md`
- 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_macro_upsert_runner.sh`
  - `PYTHONPATH=/Users/woody/ai/stockanalysis/src python3 -m stockanalysis.ingest.cli macro-upsert --series-id CPIAUCSL --series-json tests/fixtures/fred_series_CPIAUCSL.json --observations-json tests/fixtures/fred_observations_CPIAUCSL.json`
- 다시 찾기 싫은 배경지식:
  - `macro-ingest`는 SQL output까지만 구현했고, 이번 task는 actual execute를 추가하는 단계다.
