# Task Plan

이 문서는 guided single-agent보다 더 구조화된 실행이 필요한 작업에서 사용한다.

## Task

- 이름: seed-bootstrap
- 요청: priority 1 schema 위에 최소 reference/data_source seed와 검증 경로를 추가한다.
- 담당: Codex
- 날짜: 2026-04-18

## Goal

- 이 작업이 끝났을 때 달성되어야 하는 상태: 빈 DB에 migration과 최소 seed를 적용해 ingest 출발점이 보장되고, seed 범위가 문서와 검증 스크립트로 고정되어 있다.

## Why This Needs A Plan

- 왜 `contract.md`만으로 부족한가: seed는 너무 많이 넣으면 오염되고 너무 적게 넣으면 쓸모가 없다. 기준정보, 시장 범위, 검증 경로를 함께 조정해야 하므로 범위 제어가 필요하다.

## Architecture Or Approach

- 접근 방식:
  - migration과 seed를 분리한다.
  - seed는 미국 시장 MVP 기준 reference data와 stable public source 목록만 포함한다.
  - 검증은 기존 migration script를 재사용하는 wrapper 방식으로 간다.
- 핵심 tradeoff:
  - seed를 풍부하게 넣는 대신, 후속 ingest 설계에 필요한 최소 범위만 넣는다.
- 피해야 할 함정:
  - instrument universe나 theme taxonomy까지 seed에 섞는 것
  - 실제 vendor 선택이 끝나지 않았는데 상용 소스를 canonical seed로 박는 것

## Milestones

### Milestone 1

- 목표: seed 범위를 고정한다.
- 산출물: `db/seeds/README.md`, seed policy 반영 문서
- 검증: business data와 reference data가 분리되어 있어야 한다.

### Milestone 2

- 목표: reference/data_source seed SQL을 작성한다.
- 산출물: `0001_reference_seed.sql`, `0002_data_sources_seed.sql`
- 검증: 기존 priority 1 schema에 의존성 오류 없이 적용 가능해야 한다.

### Milestone 3

- 목표: migration + seed 검증을 자동화한다.
- 산출물: `scripts/verify_seed_bootstrap.sh`, handoff/review 갱신
- 검증: Docker 기반 임시 Postgres에 seed까지 적용되고 row count가 출력된다.

## Dependencies

- 선행 조건:
  - `ddl-skeleton` task 완료
  - `db/migrations/` 존재
- 순서 제약:
  - migration 없이는 seed를 적용할 수 없다
  - reference market seed 없이 exchange seed를 넣으면 안 된다

## Ownership

- 한 번에 누가 무엇을 책임지는가: 단일 agent가 seed 범위 결정, SQL 작성, 검증 스크립트 갱신을 책임진다.
- 병렬 가능한가: 현재 범위가 작아 병렬화 이득이 적다.

## Checkpoints

- 언제 상태를 다시 평가할 것인가:
  - seed SQL 작성 후
  - 실제 적용 검증 후
- 언제 handoff를 갱신할 것인가:
  - 검증 결과 확인 직후

## Verification Gates

- milestone별 통과 조건:
  - seed 범위가 최소 reference/bootstrap 수준에 머문다
  - seed SQL이 idempotent하다
  - verify wrapper가 존재한다
- 최종 통과 조건:
  - `bash scripts/verify_seed_bootstrap.sh` 성공
  - `awh verify --task seed-bootstrap` 성공
  - placeholder 없음

## Rollback

- 어느 지점까지 되돌릴 수 있는가: 공급자 seed가 논쟁적이면 `0002_data_sources_seed.sql`만 후퇴시키고 reference seed만 남길 수 있다.

## Open Questions

- 질문:
  - instrument universe seed를 바로 붙일지 별도 task로 분리할지
- 임시 가정:
  - instrument universe는 `ingest-bootstrap` 또는 `universe-bootstrap` task로 분리한다.
