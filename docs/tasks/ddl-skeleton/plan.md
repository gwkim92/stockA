# Task Plan

이 문서는 guided single-agent보다 더 구조화된 실행이 필요한 작업에서 사용한다.

## Task

- 이름: ddl-skeleton
- 요청: priority 1 schema를 실제 Postgres migration skeleton으로 구현하고 검증한다.
- 담당: Codex
- 날짜: 2026-04-18

## Goal

- 이 작업이 끝났을 때 달성되어야 하는 상태: schema design이 SQL 파일과 검증 스크립트로 concretize되어 다음 단계에서 seed/ingest/DDL refinement로 바로 이어질 수 있다.

## Why This Needs A Plan

- 왜 `contract.md`만으로 부족한가: 테이블 수가 많고 FK 순서, PK 전략, 인덱스 분리, 실제 적용 검증까지 포함되므로, 순서를 잘못 잡으면 migration 자체가 깨질 수 있다.

## Architecture Or Approach

- 접근 방식:
  - schema bootstrap, table creation, index creation을 분리한다.
  - priority 1만 구현한다.
  - Postgres best practice에 맞춰 surrogate key는 bigint identity, 시계열은 composite PK로 간다.
- 핵심 tradeoff:
  - conceptual 문서의 uuid 표현보다 실제 Postgres 성능과 운용 단순성을 우선한다.
- 피해야 할 함정:
  - FK 인덱스를 빼먹는 것
  - priority 2/3 범위를 섞어서 첫 migration을 과도하게 키우는 것
  - 실제 DB 적용 검증 없이 완료를 주장하는 것

## Milestones

### Milestone 1

- 목표: migration 구조와 PK 전략을 고정한다.
- 산출물: `db/README.md`, `0001_bootstrap.sql` 초안
- 검증: 파일 구조와 적용 순서가 명확해야 한다.

### Milestone 2

- 목표: priority 1 table DDL을 작성한다.
- 산출물: `0002_priority_1_tables.sql`
- 검증: FK 참조 순서가 논리적으로 맞고 schema design과 대응된다.

### Milestone 3

- 목표: 인덱스와 실제 적용 검증 경로를 추가한다.
- 산출물: `0003_priority_1_indexes.sql`, `scripts/verify_migrations.sh`
- 검증: Docker 기반 임시 Postgres에 migration이 적용된다.

## Dependencies

- 선행 조건:
  - `docs/db-schema-design.md`
  - `db-schema-design` task 문서
- 순서 제약:
  - schema/bootstrap보다 table creation이 앞서면 안 된다
  - table creation보다 index creation이 앞서면 안 된다
  - verification script는 migration 파일 경로가 고정된 뒤 작성한다

## Ownership

- 한 번에 누가 무엇을 책임지는가: 단일 agent가 schema translation, SQL 작성, 적용 검증을 모두 책임진다.
- 병렬 가능한가: 지금은 순서 의존성이 강해 병렬화 이득이 작다.

## Checkpoints

- 언제 상태를 다시 평가할 것인가:
  - table DDL 작성 직후
  - Docker 적용 검증 직후
- 언제 handoff를 갱신할 것인가:
  - 검증 결과가 나온 직후

## Verification Gates

- milestone별 통과 조건:
  - migration 파일 구조가 존재한다
  - priority 1 테이블이 SQL로 내려왔다
  - index 파일과 verify script가 있다
- 최종 통과 조건:
  - `bash scripts/verify_migrations.sh` 성공
  - `awh verify --task ddl-skeleton` 성공
  - placeholder 없음

## Rollback

- 어느 지점까지 되돌릴 수 있는가: index migration과 일부 제약은 필요시 제거하고 table skeleton만 남기는 단계까지 후퇴 가능하다.

## Open Questions

- 질문:
  - bootstrap 단계에서 extension을 둘 것인가
- 임시 가정:
  - 현재 priority 1에서는 extension 없이 진행한다.
