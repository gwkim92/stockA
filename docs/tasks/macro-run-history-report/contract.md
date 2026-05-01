# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: macro-run-history-report
- 요청: 최근 macro upsert 실행 이력을 canonical Postgres에서 조회하는 report/audit 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-18

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `macro-run-history` CLI가 최근 macro upsert run 목록과 status 집계, per-run observation count를 JSON으로 반환한다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: 적재를 잘하고 있는지 계속 검토하려면 실제 run 이력과 series별 결과를 쉽게 조회할 수 있어야 한다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/ingest/psql.py`
  - `src/stockanalysis/ingest/macro/upsert.py`
  - `src/stockanalysis/ingest/cli.py`
  - `db/migrations/0002_priority_1_tables.sql`
- 관련 문서:
  - `docs/macro-upsert-runner.md`
  - `docs/macro-batch-upsert.md`
  - `docs/verification-plan.md`
- 이전 결정:
  - macro 적재는 `ops.pipeline_run`을 남긴다.
  - observation은 `source_run_id`로 run과 연결된다.
  - batch 적재도 series별 run을 유지한다.

## Scope

- 포함:
  - recent macro run history query
  - CLI report entrypoint
  - unit/integration verification
  - report 문서와 task artifact
- 제외:
  - 웹 UI
  - run delete/cleanup
  - batch parent entity 추가
  - live FRED smoke

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/macro-run-history-report.md`
  - `docs/verification-plan.md`
  - `docs/plans/2026-04-18-macro-run-history-report.md`
  - `docs/tasks/macro-run-history-report/`
  - `docs/tasks/macro-batch-upsert/handoff.md`
  - `scripts/verify_macro_run_history_report.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/macro/report.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_macro_report.py`
- 수정 금지 파일:
  - migrations and seeds
  - upsert runner behavior
- 검증에 사용할 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_macro_run_history_report.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task macro-run-history-report`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`

## Deliverables

- 필수 결과물:
  - `src/stockanalysis/ingest/macro/report.py`
  - `scripts/verify_macro_run_history_report.sh`
  - `tests/test_macro_report.py`
  - `docs/macro-run-history-report.md`
  - `docs/tasks/macro-run-history-report/contract.md`
  - `docs/tasks/macro-run-history-report/plan.md`
  - `docs/tasks/macro-run-history-report/handoff.md`
- 선택 결과물:
  - `docs/tasks/macro-run-history-report/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] run history report가 `run_count`, `status_counts`, `runs`를 반환한다
- [x] per-run observation count가 포함된다
- [x] batch 적재 후 history 조회 검증 경로가 있다

## Verification Plan

- 자동 검증: `bash scripts/verify_macro_run_history_report.sh`, `awh verify --task macro-run-history-report`, placeholder 검색
- 수동 검증: `docs/macro-run-history-report.md`가 report shape와 current limits를 분명히 설명하는지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: unit/integration 검증 통과, batch upsert 후 report JSON 확인, readiness 검증 통과

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `macro-run-history` command와 `report.py`만 제거하면 기존 upsert 흐름은 유지된다.

## Open Questions

- 질문: 장기적으로 batch parent entity가 생기면 report를 run-level에서 batch-level로도 보여줄지
- 답이 없을 때 적용할 임시 가정: 현재는 series별 run history만 보여준다.
