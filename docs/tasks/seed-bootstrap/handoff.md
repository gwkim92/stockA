# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: seed-bootstrap
- 담당: Codex
- 날짜: 2026-04-18

## Current Status

- 완료:
  - `seed-bootstrap` task를 scaffold했다.
  - `db/seeds/` 아래에 reference seed와 data source seed를 추가했다.
  - `scripts/verify_seed_bootstrap.sh`를 추가했다.
  - `verify_migrations.sh`가 seed 포함 검증도 지원하도록 확장했다.
  - Docker 기반 migration + seed 적용 검증과 하네스 readiness 검증을 통과했다.
- 진행 중:
  - 다음 단계 task로 `ingest-bootstrap`이 진행 중이다.
- 막힌 점:
  - 없음.

## Files Touched

- 생성:
  - `db/seeds/README.md`
  - `db/seeds/0001_reference_seed.sql`
  - `db/seeds/0002_data_sources_seed.sql`
  - `scripts/verify_seed_bootstrap.sh`
  - `docs/tasks/seed-bootstrap/contract.md`
  - `docs/tasks/seed-bootstrap/plan.md`
  - `docs/tasks/seed-bootstrap/handoff.md`
  - `docs/tasks/seed-bootstrap/review.md`
- 수정:
  - `README.md`
  - `db/README.md`
  - `scripts/verify_migrations.sh`
  - `docs/db-schema-design.md`
  - `docs/verification-plan.md`
  - `docs/tasks/ddl-skeleton/handoff.md`
- 의도적으로 안 건드린 것:
  - instrument universe seed
  - classification/theme seed
  - app runtime 및 ingest 코드

## Decisions

- 결정:
  - seed 범위는 미국 시장 기준 `market`, `exchange`, `data_source`까지만 넣는다.
  - 검증은 기존 migration script를 재사용하는 wrapper 방식으로 구현한다.
  - 상용 vendor seed는 아직 넣지 않는다.
- 이유:
  - 현재 목표는 ingest 시작점 확보이지, 도메인 데이터 전체를 seed로 박는 것이 아니다.
  - 아직 data vendor 최종 선택이 끝나지 않았다.

## Verification Already Run

- 명령: `/tmp/agent-work-harness/scripts/new-task.sh backend /Users/woody/ai/stockanalysis seed-bootstrap --with-plan`
- 관찰한 결과: task scaffold가 생성되었다.

- 명령: `bash /Users/woody/ai/stockanalysis/scripts/verify_seed_bootstrap.sh`
- 관찰한 결과:
  - migration 3개와 seed 2개가 순서대로 적용되었다.
  - seeded row count는 `ref.market=1`, `ref.exchange=3`, `ingest.data_source=6`으로 출력되었다.

- 명령: `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task seed-bootstrap`
- 관찰한 결과: `Task seed-bootstrap passed readiness checks.`

- 명령: `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 관찰한 결과: placeholder 출력이 없었다.

## Still Unverified

- 항목: instrument universe bootstrap
- 왜 중요한가: seed만으로는 실제 종목 적재나 추천 실험을 시작할 수 없다.

- 항목: market data ingest bootstrap
- 왜 중요한가: ref/data_source seed 다음 단계는 실제 price/financial/macro 적재 흐름을 잡는 일이다.

## Exact Next Step

- 다음 세션은 이것부터 시작: `docs/tasks/ingest-bootstrap/`와 `src/stockanalysis/ingest/`를 읽고, 첫 실제 데이터 적재 경로를 어떤 소스부터 구현할지 정한다.

## Risks

- 위험:
  - 시장 범위를 미국으로 먼저 seed한 선택이 향후 한국 시장 우선 전략과 어긋날 수 있다.
  - 아직 instrument universe가 없어서 seed만으로는 실제 종목 적재를 시작할 수 없다.
- 대응:
  - 한국 시장 seed는 별도 파일로 추가 가능하게 분리했다.
  - 다음 task에서 universe/bootstrap을 별도로 설계한다.

## Useful Context

- 파일:
  - `db/seeds/0001_reference_seed.sql`
  - `db/seeds/0002_data_sources_seed.sql`
  - `scripts/verify_seed_bootstrap.sh`
  - `docs/tasks/ddl-skeleton/handoff.md`
- 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_seed_bootstrap.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task seed-bootstrap`
- 다시 찾기 싫은 배경지식:
  - seed는 reference/bootstrap만 포함한다.
  - instrument universe와 classification taxonomy는 의도적으로 뒤에 분리했다.
