# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: ddl-skeleton
- 담당: Codex
- 날짜: 2026-04-18

## Current Status

- 완료:
  - `ddl-skeleton` task를 scaffold했다.
  - `db/migrations/`에 bootstrap, priority 1 tables, priority 1 indexes SQL을 추가했다.
  - `scripts/verify_migrations.sh`를 추가해 Docker 기반 임시 Postgres 적용 검증 경로를 만들었다.
  - `docs/db-schema-design.md`에 PK 전략 구현 메모를 반영했다.
  - Docker 기반 migration 적용 검증과 하네스 readiness 검증을 통과했다.
- 진행 중:
  - 다음 단계 task로 `seed-bootstrap`이 진행 중이다.
- 막힌 점:
  - 없음. 다만 Docker image pull이 처음이면 시간이 걸릴 수 있다.

## Files Touched

- 생성:
  - `db/README.md`
  - `db/migrations/0001_bootstrap.sql`
  - `db/migrations/0002_priority_1_tables.sql`
  - `db/migrations/0003_priority_1_indexes.sql`
  - `scripts/verify_migrations.sh`
  - `docs/tasks/ddl-skeleton/contract.md`
  - `docs/tasks/ddl-skeleton/plan.md`
  - `docs/tasks/ddl-skeleton/handoff.md`
  - `docs/tasks/ddl-skeleton/review.md`
- 수정:
  - `README.md`
  - `docs/db-schema-design.md`
  - `docs/verification-plan.md`
  - `docs/tasks/db-schema-design/handoff.md`
- 의도적으로 안 건드린 것:
  - seed data
  - priority 2/3 schema
  - app code 및 ORM

## Decisions

- 결정:
  - migration은 bootstrap/table/index 3단 분리로 구성한다.
  - surrogate key는 bigint identity를 사용한다.
  - 시계열/junction 테이블은 composite PK를 유지한다.
  - FK 인덱스는 별도 migration 파일에서 명시적으로 추가한다.
- 이유:
  - Postgres best practice와 실제 운영 단순성을 맞추기 위해서다.
  - priority 1 범위를 명확히 유지하면서도 다음 migration 확장을 쉽게 하기 위해서다.

## Verification Already Run

- 명령: `/tmp/agent-work-harness/scripts/new-task.sh backend /Users/woody/ai/stockanalysis ddl-skeleton --with-plan`
- 관찰한 결과: task scaffold가 생성되었다.

- 명령: `bash /Users/woody/ai/stockanalysis/scripts/verify_migrations.sh`
- 관찰한 결과:
  - `0001_bootstrap.sql`, `0002_priority_1_tables.sql`, `0003_priority_1_indexes.sql`가 순서대로 적용되었다.
  - `ops`, `ref`, `ingest`, `market`, `macro`, `event`, `signal`, `portfolio` schema의 priority 1 테이블이 생성되었다.

- 명령: `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task ddl-skeleton`
- 관찰한 결과: `Task ddl-skeleton passed readiness checks.`

- 명령: `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 관찰한 결과: placeholder 출력이 없었다.

## Still Unverified

- 항목: priority 1 seed/bootstrap 전략
- 왜 중요한가: schema만 있고 seed가 없으면 실제 ingest 또는 query 개발을 바로 시작하기 어렵다.

- 항목: ingest pipeline 시작 순서
- 왜 중요한가: 시장 데이터부터 넣을지, ref/master data seed부터 넣을지 결정해야 구현 순서가 안정된다.

## Exact Next Step

- 다음 세션은 이것부터 시작: `docs/tasks/seed-bootstrap/`와 `db/seeds/`를 읽고, 초기 reference seed와 ingest bootstrap의 연결 범위를 확정한다.

## Risks

- 위험:
  - conceptual schema 문서의 일부 uuid 표기와 실제 bigint identity 구현이 혼동을 줄 수 있다.
  - 실제 공급자 데이터에 맞춰 일부 컬럼은 후속 migration에서 조정될 수 있다.
- 대응:
  - `docs/db-schema-design.md`에 PK strategy 구현 메모를 추가했다.
  - 공급자별 차이는 이후 seed/ingest task에서 조정한다.

## Useful Context

- 파일:
  - `docs/db-schema-design.md`
  - `db/README.md`
  - `db/migrations/0002_priority_1_tables.sql`
  - `db/migrations/0003_priority_1_indexes.sql`
- 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_migrations.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task ddl-skeleton`
- 다시 찾기 싫은 배경지식:
  - 이 단계는 priority 1 canonical schema만 구현한다.
  - priority 2/3와 seed data는 의도적으로 뒤로 밀었다.
