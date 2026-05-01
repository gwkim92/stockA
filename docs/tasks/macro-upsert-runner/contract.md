# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: macro-upsert-runner
- 요청: `macro-sync`가 만든 정규화 결과를 canonical Postgres에 실행하고 `ops.pipeline_run`과 연결하는 첫 DB upsert 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-18

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: fixture 기반 macro payload를 `macro-upsert` CLI로 canonical Postgres에 반영할 수 있고, `ops.pipeline_run`에 성공/실패 상태가 기록된다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: 정규화 결과가 실제 저장되지 않으면 이후 사이클 엔진, thesis 엔진, 성과 추적이 참조할 canonical macro 시계열이 생기지 않는다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/macro/fred.py`
  - `src/stockanalysis/ingest/macro/sql.py`
  - `db/migrations/0002_priority_1_tables.sql`
- 관련 문서:
  - `docs/macro-ingest.md`
  - `docs/verification-plan.md`
  - `docs/tasks/macro-ingest/handoff.md`
- 이전 결정:
  - 첫 실제 ingest는 `macro`부터 시작한다.
  - `macro-ingest`는 SQL 생성까지만 구현했다.
  - direct execute와 pipeline run 연결은 다음 task로 미뤘다.

## Scope

- 포함:
  - `psql` 명령 기반 DB 실행기
  - `ops.pipeline_run` 생성/종료 처리
  - `macro-upsert` CLI
  - fixture 기반 DB upsert 검증
  - task/verification 문서 갱신
- 제외:
  - batch multi-series 실행
  - scheduler
  - ALFRED revision 처리
  - live fetch smoke

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `.env.example`
  - `docs/macro-upsert-runner.md`
  - `docs/verification-plan.md`
  - `docs/tasks/macro-ingest/handoff.md`
  - `docs/tasks/macro-upsert-runner/`
  - `docs/plans/2026-04-18-macro-upsert-runner.md`
  - `scripts/verify_macro_upsert_runner.sh`
  - `src/stockanalysis/ingest/config.py`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/psql.py`
  - `src/stockanalysis/ingest/macro/sql.py`
  - `src/stockanalysis/ingest/macro/upsert.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_macro_upsert.py`
- 수정 금지 파일:
  - existing migrations and seeds
  - 외부 하네스 원본 저장소
- 검증에 사용할 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_macro_upsert_runner.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task macro-upsert-runner`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`

## Deliverables

- 필수 결과물:
  - `src/stockanalysis/ingest/psql.py`
  - `src/stockanalysis/ingest/macro/upsert.py`
  - `scripts/verify_macro_upsert_runner.sh`
  - `tests/test_macro_upsert.py`
  - `docs/macro-upsert-runner.md`
  - `docs/tasks/macro-upsert-runner/contract.md`
  - `docs/tasks/macro-upsert-runner/plan.md`
  - `docs/tasks/macro-upsert-runner/handoff.md`
- 선택 결과물:
  - `docs/tasks/macro-upsert-runner/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] `macro-upsert`가 `ops.pipeline_run`을 생성한다
- [x] `macro.observation.source_run_id`가 pipeline run과 연결된다
- [x] fixture 기반 integration 검증 경로가 존재한다

## Verification Plan

- 자동 검증: `bash scripts/verify_macro_upsert_runner.sh`, `awh verify --task macro-upsert-runner`, placeholder 검색
- 수동 검증: `docs/macro-upsert-runner.md`에서 env var contract와 현재 제한사항이 명확한지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: unit/integration 검증 통과, pipeline run status와 macro row count 확인, task readiness 검증 통과

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `macro-upsert` command와 `psql.py`를 제거하고 기존 `macro-sync` SQL output 경로만 유지하면 된다.

## Open Questions

- 질문: 장기적으로 `psql` command path를 유지할지 Python DB driver로 전환할지
- 답이 없을 때 적용할 임시 가정: 현재는 무의존성과 검증 단순성을 위해 `psql` command path를 유지한다.
