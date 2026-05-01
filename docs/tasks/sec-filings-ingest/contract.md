# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: sec-filings-ingest
- 요청: SEC submissions API에서 filing 메타데이터를 읽어 `ingest.source_document`에 적재하는 첫 공시 ingest 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-18

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `sec-filings-upsert` CLI가 CIK 기준 filing 메타데이터를 canonical Postgres에 적재하고 `ops.pipeline_run`에 실행 이력을 남긴다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: 이벤트 분석과 정책/실적 해석은 먼저 원문 메타데이터를 모아야 시작할 수 있으므로, `source_document` 적재가 비정형 데이터 파이프라인의 출발점이다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/ingest/sources/sec.py`
  - `src/stockanalysis/ingest/psql.py`
  - `src/stockanalysis/ingest/cli.py`
  - `db/migrations/0002_priority_1_tables.sql`
- 관련 문서:
  - `docs/ingest-bootstrap.md`
  - `docs/verification-plan.md`
  - `docs/tasks/macro-run-history-report/handoff.md`
- 이전 결정:
  - canonical write는 `psql` command wrapper를 사용한다.
  - `source_document`는 비정형 원문 메타데이터의 첫 저장소다.
  - 현재 단계는 issuer/instrument mapping 없이 document metadata만 다룬다.

## Scope

- 포함:
  - SEC submissions payload 정규화
  - `ingest.source_document` upsert SQL
  - `sec-filings-sync`, `sec-filings-upsert` CLI
  - fixture 기반 DB upsert 검증
  - task/verification 문서 갱신
- 제외:
  - filing body/raw artifact 저장
  - companyfacts ingest
  - issuer/instrument mapping
  - event extraction

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/sec-filings-ingest.md`
  - `docs/verification-plan.md`
  - `docs/plans/2026-04-18-sec-filings-ingest.md`
  - `docs/tasks/sec-filings-ingest/`
  - `docs/tasks/macro-run-history-report/handoff.md`
  - `scripts/verify_sec_filings_ingest.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/sec/`
  - `tests/test_ingest_cli.py`
  - `tests/test_sec_filings.py`
  - `tests/fixtures/sec_submissions_CIK0000320193.json`
- 수정 금지 파일:
  - migrations and seeds
  - macro ingest code
- 검증에 사용할 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_sec_filings_ingest.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task sec-filings-ingest`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`

## Deliverables

- 필수 결과물:
  - `src/stockanalysis/ingest/sec/`
  - `scripts/verify_sec_filings_ingest.sh`
  - `tests/test_sec_filings.py`
  - `docs/sec-filings-ingest.md`
  - `docs/tasks/sec-filings-ingest/contract.md`
  - `docs/tasks/sec-filings-ingest/plan.md`
  - `docs/tasks/sec-filings-ingest/handoff.md`
- 선택 결과물:
  - `docs/tasks/sec-filings-ingest/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] filing 메타데이터가 `source_document`에 적재된다
- [x] `ingested_by_run_id`가 pipeline run과 연결된다
- [x] fixture 기반 SEC filings 검증 경로가 존재한다

## Verification Plan

- 자동 검증: `bash scripts/verify_sec_filings_ingest.sh`, `awh verify --task sec-filings-ingest`, placeholder 검색
- 수동 검증: `docs/sec-filings-ingest.md`가 current mapping과 current limits를 분명히 설명하는지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: unit/integration 검증 통과, source_document row count 확인, readiness 검증 통과

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `sec-filings-*` command와 `src/stockanalysis/ingest/sec/`만 제거하면 기존 macro ingest 경로는 유지된다.

## Open Questions

- 질문: 향후 filing body/raw artifact 저장소를 `raw_storage_uri`에 연결할지 별도 테이블로 둘지
- 답이 없을 때 적용할 임시 가정: 현재는 metadata only로 두고 raw artifact는 후속 task에서 분리한다.
