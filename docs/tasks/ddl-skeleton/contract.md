# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: ddl-skeleton
- 요청: `docs/db-schema-design.md`의 priority 1 범위를 실제 Postgres migration skeleton으로 구현하고, 로컬에서 적용 검증 가능한 스크립트까지 추가한다.
- 담당: Codex
- 날짜: 2026-04-18

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: priority 1 schema가 `db/migrations/`에 SQL로 존재하고, migration 적용 순서와 검증 방법이 repo에 남아 있으며, 임시 Postgres에 실제로 적용 가능한 상태다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: 설계 문서만으로는 개발이 시작되지 않는다. 데이터 적재, cycle engine, recommendation engine 구현으로 이어지려면 canonical schema가 실제 SQL 초안으로 존재해야 한다.

## Inputs

- 관련 코드: 현재 앱 코드는 없고, 이번 작업이 첫 SQL skeleton 추가 단계다.
- 관련 문서:
  - `docs/db-schema-design.md`
  - `docs/verification-plan.md`
  - `docs/tasks/db-schema-design/handoff.md`
  - `docs/tasks/db-schema-design/review.md`
- 이전 결정:
  - priority 1 테이블만 먼저 구현한다.
  - canonical store는 Postgres다.
  - surrogate key는 구현 단계에서 `bigint identity` 중심으로 구체화한다.

## Scope

- 포함:
  - `db/` 디렉터리 구조 추가
  - schema bootstrap SQL
  - priority 1 table SQL
  - priority 1 index SQL
  - migration 검증 스크립트
  - 관련 handoff/review 문서 갱신
- 제외:
  - actual ORM model
  - app runtime integration
  - seed data 작성
  - priority 2/3 테이블 구현

## Mutable Surface

여러 경로가 있으면 값은 다음 줄 bullet list로 적어도 된다.

- 수정 가능한 파일:
  - `README.md`
  - `docs/db-schema-design.md`
  - `docs/verification-plan.md`
  - `docs/tasks/db-schema-design/handoff.md`
  - `docs/tasks/ddl-skeleton/contract.md`
  - `docs/tasks/ddl-skeleton/plan.md`
  - `docs/tasks/ddl-skeleton/handoff.md`
  - `docs/tasks/ddl-skeleton/review.md`
  - `db/README.md`
  - `db/migrations/*.sql`
  - `scripts/verify_migrations.sh`
- 수정 금지 파일:
  - priority 2/3 범위 설계 문서
  - 앱 코드, 테스트, ingest 구현체
  - 외부 하네스 원본 저장소(`/tmp/agent-work-harness`) 내부 파일
- 검증에 사용할 명령:
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task ddl-skeleton`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_migrations.sh`

## Deliverables

- 필수 결과물:
  - `db/README.md`
  - `db/migrations/0001_bootstrap.sql`
  - `db/migrations/0002_priority_1_tables.sql`
  - `db/migrations/0003_priority_1_indexes.sql`
  - `scripts/verify_migrations.sh`
  - `docs/tasks/ddl-skeleton/handoff.md`
- 선택 결과물:
  - schema design 문서 보완

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다

작업 전용 체크를 아래에 추가한다.

- [x] priority 1 테이블이 schema 설계 문서와 대응된다
- [x] FK 인덱스와 주요 unique index가 별도 migration에 정리된다
- [x] 임시 Postgres 적용 검증 경로가 repo에 존재한다

## Verification Plan

- 자동 검증:
  - `awh verify --task ddl-skeleton`
  - placeholder 검색
  - `bash scripts/verify_migrations.sh`
- 수동 검증:
  - SQL 파일이 `docs/db-schema-design.md`의 priority 1 범위와 실제로 대응되는지 확인
- 브라우저, 로그, metric 검증:
  - 없음. 현재는 DB schema bootstrap 단계다
- 어떤 증거가 있어야 완료로 간주하는가:
  - migration이 에러 없이 적용된다
  - task readiness 검증이 통과한다
  - 남은 priority 2/3와 deferred items가 분리되어 있다

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: 문제를 일으키는 migration 파일을 우선순위 1 범위로 다시 축소하고, 불확실한 제약이나 인덱스는 별도 후속 migration으로 미룬다.

## Open Questions

- 질문: priority 1 migration을 한 번에 적용할지, schema/table/index를 분리할지
- 답이 없을 때 적용할 임시 가정: bootstrap/table/index 3단 분리로 유지한다.

- 질문: PK 전략을 uuid로 유지할지 bigint identity로 concretize할지
- 답이 없을 때 적용할 임시 가정: 단일 Postgres 운영 기준으로 bigint identity를 사용한다.
