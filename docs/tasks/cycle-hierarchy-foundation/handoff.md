# Session Handoff

## Current Status

- 완료:
  - `db/seeds/0004_cycle_hierarchy_seed.sql`로 거시/도메인/테마 계층 노드와 edge를 추가했다.
  - `QUBT` starter instrument와 핵심 종목 factor exposure를 추가했다.
  - ontology validation allowed relation type에 `hierarchy`, `macro_to_domain`, `macro_to_theme`, `domain_to_theme` 등 계층형 relation을 추가했다.
  - seed 검증 테스트를 추가했다.
- 막힌 점:
  - 없음.

## Exact Next Step

- exact next step: EC2에 최신 commit을 배포하고 `0004_cycle_hierarchy_seed.sql`을 적용한 뒤 DB row count를 확인한다.
