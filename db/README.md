# Database Migrations

이 디렉터리는 이 프로젝트의 Postgres canonical schema migration 초안을 둔다.

현재 범위:

- priority 1 MVP 테이블
- schema bootstrap
- 기본 FK/조회 인덱스
- 최소 seed bootstrap

파일 순서:

1. `migrations/0001_bootstrap.sql`
2. `migrations/0002_priority_1_tables.sql`
3. `migrations/0003_priority_1_indexes.sql`

seed 순서:

1. `seeds/0001_reference_seed.sql`
2. `seeds/0002_data_sources_seed.sql`

검증:

```bash
bash scripts/verify_migrations.sh
bash scripts/verify_seed_bootstrap.sh
```

원칙:

- canonical 운영 상태는 Postgres에 저장한다.
- wide analytical table과 backtest join 결과는 이후 별도 분석 스토어로 분리한다.
- 이 migration 세트는 `docs/db-schema-design.md`의 priority 1 범위만 구현한다.
- seed는 현재 미국 시장 MVP 기준만 담는다.
