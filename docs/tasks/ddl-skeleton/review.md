# Review Notes

이 문서는 generator와 분리된 evaluator artifact다.

코드, diff, 구조, 리스크 관점에서 변경을 검토할 때 사용한다.

## Review Scope

- 대상 task: `ddl-skeleton`
- 검토 대상 파일:
  - `db/README.md`
  - `db/migrations/0001_bootstrap.sql`
  - `db/migrations/0002_priority_1_tables.sql`
  - `db/migrations/0003_priority_1_indexes.sql`
  - `scripts/verify_migrations.sh`
  - `docs/tasks/ddl-skeleton/contract.md`
  - `docs/tasks/ddl-skeleton/handoff.md`
- 검토 기준:
  - priority 1 범위 준수
  - FK 인덱스 누락 여부
  - 실제 적용 검증 경로 존재 여부
  - conceptual schema와의 정합성

## Claimed Outcome

- generator가 주장하는 완료 내용: priority 1 canonical schema가 실제 Postgres migration skeleton으로 구현되었고, Docker 기반 적용 검증 경로까지 repo에 포함되었다.

## Evidence Checked

- 읽은 파일:
  - `docs/db-schema-design.md`
  - `db/README.md`
  - `db/migrations/0001_bootstrap.sql`
  - `db/migrations/0002_priority_1_tables.sql`
  - `db/migrations/0003_priority_1_indexes.sql`
  - `scripts/verify_migrations.sh`
- 실행한 명령:
  - `/tmp/agent-work-harness/scripts/new-task.sh backend /Users/woody/ai/stockanalysis ddl-skeleton --with-plan`
  - `find /Users/woody/ai/stockanalysis/docs/tasks -maxdepth 4 -type f | sort`
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_migrations.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task ddl-skeleton`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 확인한 로그 또는 산출물:
  - ddl-skeleton task scaffold 로그
  - SQL skeleton files
  - Docker 기반 migration 적용 로그
  - `Task ddl-skeleton passed readiness checks.`

## Findings

심각도 순으로 적는다.

- Finding: concept 문서의 일부 table spec은 uuid 기반 표현이 남아 있고, 실제 DDL은 bigint identity로 concretize되었다.
- Impact: 문서만 읽고 SQL을 안 보면 식별자 전략을 오해할 수 있다.
- Evidence: `docs/db-schema-design.md` table section vs `db/migrations/0002_priority_1_tables.sql`
- Suggested fix: 이후 schema 문서 정리 task에서 table-by-table 표기를 SQL과 완전히 맞춘다.

- Finding: priority 1까지만 구현했으므로 thesis review, recommendation score component, attribution, audit log 등은 아직 없다.
- Impact: app 구현이 바로 모든 기능을 커버하지는 못한다.
- Evidence: `docs/db-schema-design.md`의 priority 2/3 목록과 현재 migration 파일
- Suggested fix: 다음 migration task에서 priority 2부터 순차적으로 올린다.

## Residual Risks

- 아직 남아 있는 위험:
  - seed/bootstrap 전략 미정
  - priority 2/3 migration은 아직 미구현

## Open Questions

- 질문:
  - priority 1 다음 구현을 seed data bootstrap부터 시작할지 ingest pipeline부터 시작할지

## Verdict

- pass with risks
