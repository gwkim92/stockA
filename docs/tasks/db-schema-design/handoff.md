# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: db-schema-design
- 담당: Codex
- 날짜: 2026-04-18

## Current Status

- 완료:
  - `db-schema-design` task를 scaffold했다.
  - `docs/db-schema-design.md`에 storage topology, schema inventory, 핵심 테이블, MVP 우선순위를 저장했다.
  - foundation task handoff를 현재 상태로 갱신했다.
- 진행 중:
  - 다음 단계 task로 `ddl-skeleton`이 진행 중이다.
- 막힌 점:
  - 초기 시장과 실제 데이터 공급원은 아직 사용자 확정 전이다.

## Files Touched

- 생성:
  - `docs/db-schema-design.md`
  - `docs/tasks/db-schema-design/contract.md`
  - `docs/tasks/db-schema-design/plan.md`
  - `docs/tasks/db-schema-design/handoff.md`
  - `docs/tasks/db-schema-design/review.md`
- 수정:
  - `README.md`
  - `docs/tasks/foundation-architecture/handoff.md`
- 의도적으로 안 건드린 것:
  - 앱 코드, SQL migration, ORM 모델, ingest 파이프라인 구현

## Decisions

- 결정:
  - canonical 운영 저장소는 Postgres로 유지한다.
  - 대량 분석용 wide feature/backtest 데이터는 Parquet/DuckDB 보조 스토어로 분리한다.
  - 섹터/산업/테마는 `classification_node`와 `classification_edge`로 통합 모델링한다.
  - event impact는 generic polymorphic table 대신 instrument/classification 분리 테이블로 설계한다.
  - recommendation과 performance는 separate history table로 남긴다.
- 이유:
  - 추천 당시 근거와 이후 성과를 재구성하려면 typed relational model이 필요하다.
  - 초기 도메인은 변동성이 크지만, 핵심 엔터티는 이미 충분히 안정적이다.

## Verification Already Run

- 명령: `/tmp/agent-work-harness/scripts/new-task.sh research /Users/woody/ai/stockanalysis db-schema-design --with-plan`
- 관찰한 결과: contract, handoff, plan, review 템플릿이 생성되었다.

## Still Unverified

- 항목: `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task db-schema-design`
- 왜 중요한가: 새 task 문서가 하네스 기준 최소 준비 상태를 통과해야 한다.

- 항목: 실제 SQL migration 우선순위
- 왜 중요한가: 테이블이 많기 때문에 어디까지를 첫 migration 묶음으로 잡을지 결정해야 구현 속도를 통제할 수 있다.

## Exact Next Step

- 다음 세션은 이것부터 시작: `docs/tasks/ddl-skeleton/`와 `db/migrations/`를 읽고, migration 적용 검증 또는 seed/bootstrap 설계로 넘어간다.

## Risks

- 위험:
  - 데이터 공급자별 필드 차이 때문에 일부 컬럼은 실제 수집 단계에서 조정이 필요할 수 있다.
  - benchmark, 국가/정책 이벤트, embedding 저장소는 아직 미정이다.
- 대응:
  - schema 문서에 deferred decisions를 남겼다.
  - 초기 migration은 우선순위 1 테이블까지만 제한한다.

## Useful Context

- 파일:
  - `docs/project-foundation.md`
  - `docs/db-schema-design.md`
  - `docs/tasks/db-schema-design/contract.md`
  - `docs/tasks/db-schema-design/plan.md`
- 명령:
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task db-schema-design`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 다시 찾기 싫은 배경지식:
  - 이 시스템은 단순 추천기가 아니라 cycle-based investment operating system이다.
  - 스키마는 multi-market ready지만 MVP 운영 범위는 한 시장으로 제한한다.
