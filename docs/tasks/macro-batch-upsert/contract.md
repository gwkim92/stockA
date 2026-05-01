# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: macro-batch-upsert
- 요청: 여러 기본 거시 series를 한 번에 canonical Postgres에 적재하는 batch runner와 검증 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-18

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `macro-batch-upsert` CLI가 기본 series 여러 개를 순차 적재하고, series별 `pipeline_run`을 남기면서 전체 batch summary를 반환한다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: single-series upsert만으로는 초기 macro bootstrap을 매번 수동 반복해야 하므로, 실제 운영에 쓸 수 있는 ingest 시작점이 되지 못한다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/ingest/macro/upsert.py`
  - `src/stockanalysis/ingest/cli.py`
  - `scripts/verify_macro_upsert_runner.sh`
- 관련 문서:
  - `docs/macro-upsert-runner.md`
  - `docs/verification-plan.md`
  - `docs/tasks/macro-upsert-runner/handoff.md`
- 이전 결정:
  - canonical DB write는 `psql` command wrapper를 사용한다.
  - series별 `pipeline_run` 1건을 유지한다.
  - fixture 기반 deterministic 검증 경로를 우선한다.

## Scope

- 포함:
  - default macro series batch runner
  - fixture directory resolution
  - batch CLI summary
  - multi-series fixture와 integration verify
  - task/verification 문서 갱신
- 제외:
  - arbitrary custom series batch
  - parallel execution
  - retry orchestration
  - live FRED smoke

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/macro-batch-upsert.md`
  - `docs/verification-plan.md`
  - `docs/plans/2026-04-18-macro-batch-upsert.md`
  - `docs/tasks/macro-batch-upsert/`
  - `docs/tasks/macro-upsert-runner/handoff.md`
  - `scripts/verify_macro_batch_upsert.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/macro/upsert.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_macro_upsert.py`
  - `tests/fixtures/fred_series_FEDFUNDS.json`
  - `tests/fixtures/fred_observations_FEDFUNDS.json`
- 수정 금지 파일:
  - migrations and seeds
  - single-series runner 검증 스크립트
- 검증에 사용할 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_macro_batch_upsert.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task macro-batch-upsert`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`

## Deliverables

- 필수 결과물:
  - `src/stockanalysis/ingest/macro/upsert.py`
  - `scripts/verify_macro_batch_upsert.sh`
  - `tests/test_macro_upsert.py`
  - `docs/macro-batch-upsert.md`
  - `docs/tasks/macro-batch-upsert/contract.md`
  - `docs/tasks/macro-batch-upsert/plan.md`
  - `docs/tasks/macro-batch-upsert/handoff.md`
- 선택 결과물:
  - `docs/tasks/macro-batch-upsert/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] 두 개 이상 series를 한 번에 적재하는 검증 경로가 있다
- [x] batch summary에 성공/실패 개수가 포함된다
- [x] fixture directory 모드가 deterministic하게 동작한다

## Verification Plan

- 자동 검증: `bash scripts/verify_macro_batch_upsert.sh`, `awh verify --task macro-batch-upsert`, placeholder 검색
- 수동 검증: `docs/macro-batch-upsert.md`가 batch 범위와 한계를 분명히 설명하는지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: unit/integration 검증 통과, 2개 series 적재 확인, readiness 검증 통과

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `macro-batch-upsert` command와 fixture directory logic만 제거하고 single-series `macro-upsert`를 유지하면 된다.

## Open Questions

- 질문: batch failure가 있어도 전체 command를 부분 성공으로 볼지, 즉시 실패로 볼지
- 답이 없을 때 적용할 임시 가정: 현재는 모든 series를 끝까지 실행하고 summary에 실패를 남긴 뒤 non-zero exit code를 반환한다.
