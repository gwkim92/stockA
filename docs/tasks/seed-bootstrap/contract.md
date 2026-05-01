# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: seed-bootstrap
- 요청: priority 1 schema 위에 최소 시장 기준정보와 데이터 소스를 seed로 추가하고, migration과 seed를 함께 검증하는 경로를 repo에 남긴다.
- 담당: Codex
- 날짜: 2026-04-18

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 빈 DB에 migration을 적용한 뒤 최소 `market`, `exchange`, `data_source` 기준정보를 자동으로 넣을 수 있고, 이후 ingest/bootstrap 구현이 이 seed를 기반으로 바로 시작될 수 있다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: schema만 있고 기준정보가 없으면 실제 적재 파이프라인, instrument bootstrap, macro series bootstrap이 모두 첫 단계에서 막힌다. 최소 seed는 개발 시작점과 환경 일관성을 보장한다.

## Inputs

- 관련 코드:
  - `db/migrations/0001_bootstrap.sql`
  - `db/migrations/0002_priority_1_tables.sql`
  - `db/migrations/0003_priority_1_indexes.sql`
  - `scripts/verify_migrations.sh`
- 관련 문서:
  - `docs/db-schema-design.md`
  - `docs/verification-plan.md`
  - `docs/tasks/ddl-skeleton/handoff.md`
- 이전 결정:
  - MVP는 미국 시장 기준으로 좁게 시작한다.
  - priority 1 canonical schema는 이미 SQL로 구현되어 있다.
  - seed는 opinionated business data가 아니라 최소 reference/bootstrap 범위에만 한정한다.

## Scope

- 포함:
  - `db/seeds/` 디렉터리 추가
  - 미국 시장 기준 `ref.market`, `ref.exchange` seed
  - 최소 `ingest.data_source` seed
  - seed 검증 wrapper script
  - 관련 README, verification plan, task 문서 갱신
- 제외:
  - instrument universe seed
  - classification node/theme seed
  - portfolio, thesis, recommendation seed
  - 실제 ingest 구현

## Mutable Surface

여러 경로가 있으면 값은 다음 줄 bullet list로 적어도 된다.

- 수정 가능한 파일:
  - `README.md`
  - `db/README.md`
  - `db/seeds/*.sql`
  - `scripts/verify_migrations.sh`
  - `scripts/verify_seed_bootstrap.sh`
  - `docs/db-schema-design.md`
  - `docs/verification-plan.md`
  - `docs/tasks/ddl-skeleton/handoff.md`
  - `docs/tasks/seed-bootstrap/contract.md`
  - `docs/tasks/seed-bootstrap/plan.md`
  - `docs/tasks/seed-bootstrap/handoff.md`
  - `docs/tasks/seed-bootstrap/review.md`
- 수정 금지 파일:
  - priority 1 table schema SQL
  - priority 2/3 schema 문서
  - ingest runtime 구현체
- 검증에 사용할 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_seed_bootstrap.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task seed-bootstrap`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`

## Deliverables

- 필수 결과물:
  - `db/seeds/README.md`
  - `db/seeds/0001_reference_seed.sql`
  - `db/seeds/0002_data_sources_seed.sql`
  - `scripts/verify_seed_bootstrap.sh`
  - `docs/tasks/seed-bootstrap/handoff.md`
- 선택 결과물:
  - seed 범위 설명 보강

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다

작업 전용 체크를 아래에 추가한다.

- [x] 미국 시장 기준 seed가 존재한다
- [x] seed 검증이 migration 검증 위에서 재사용 가능하다
- [x] 후속 ingest/bootstrap 대상이 명확히 분리되어 있다

## Verification Plan

- 자동 검증:
  - `bash scripts/verify_seed_bootstrap.sh`
  - `awh verify --task seed-bootstrap`
  - placeholder 검색
- 수동 검증:
  - seed가 reference/bootstrap 범위에만 머물고, business logic data를 섞지 않는지 확인
- 브라우저, 로그, metric 검증:
  - 없음. DB seed bootstrap 단계다
- 어떤 증거가 있어야 완료로 간주하는가:
  - migration + seed 적용이 성공한다
  - seeded row count가 출력된다
  - task readiness 검증이 통과한다

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: 문제 있는 seed를 제거하고 migration-only 상태로 되돌린 뒤, 불확실한 공급자나 시장 정보는 후속 task로 미룬다.

## Open Questions

- 질문: 한국 시장 seed를 지금 같이 넣을지 후속 task로 미룰지
- 답이 없을 때 적용할 임시 가정: 미국 시장 MVP를 우선하고, 한국 시장 seed는 별도 task로 분리한다.

- 질문: data_source에 실제 상용 vendor를 seed로 넣을지
- 답이 없을 때 적용할 임시 가정: 현재는 공용/공식 소스와 내부 수동 소스만 넣는다.
