# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: ingest-bootstrap
- 요청: 실제 외부 데이터 수집기를 위한 첫 코드 골격과 소스 레지스트리, CLI, 검증 경로를 repo에 추가한다.
- 담당: Codex
- 날짜: 2026-04-18

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: SEC, FRED, Alpha Vantage를 대상으로 한 source adapter/request builder/CLI 구조가 존재하고, 이후 실제 DB 적재 단계가 이 구조 위에서 이어질 수 있다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: seed와 스키마만으로는 실제 투자 데이터가 들어오지 않는다. 시장/거시/공시 데이터를 주기적으로 가져오는 collector 계층이 있어야 프로젝트가 정적인 설계에서 운영 가능한 시스템으로 넘어간다.

## Inputs

- 관련 코드:
  - `db/seeds/0002_data_sources_seed.sql`
  - `scripts/verify_seed_bootstrap.sh`
- 관련 문서:
  - `docs/db-schema-design.md`
  - `docs/ingest-bootstrap.md`
  - `docs/verification-plan.md`
  - `docs/tasks/seed-bootstrap/handoff.md`
- 이전 결정:
  - seed는 reference/bootstrap만 포함한다.
  - 실제 market/macro/filings 데이터는 collector가 가져와야 한다.
  - 초기 소스는 SEC, FRED, Alpha Vantage 중심으로 좁힌다.

## Scope

- 포함:
  - Python project bootstrap
  - ingest source adapters
  - source registry
  - request builder CLI
  - ingest bootstrap 문서
  - 기본 unit test와 verification script
- 제외:
  - 실제 DB upsert 구현
  - scheduler/cron
  - retry queue/persistence
  - actual universe ingestion
  - 뉴스 ingestion

## Mutable Surface

여러 경로가 있으면 값은 다음 줄 bullet list로 적어도 된다.

- 수정 가능한 파일:
  - `README.md`
  - `pyproject.toml`
  - `.env.example`
  - `docs/ingest-bootstrap.md`
  - `docs/verification-plan.md`
  - `docs/tasks/seed-bootstrap/handoff.md`
  - `docs/tasks/ingest-bootstrap/contract.md`
  - `docs/tasks/ingest-bootstrap/plan.md`
  - `docs/tasks/ingest-bootstrap/handoff.md`
  - `docs/tasks/ingest-bootstrap/review.md`
  - `src/stockanalysis/**`
  - `tests/**`
  - `scripts/verify_ingest_bootstrap.sh`
  - `db/seeds/0002_data_sources_seed.sql`
- 수정 금지 파일:
  - priority 1 schema SQL
  - classification/theme seed
  - portfolio/thesis runtime
- 검증에 사용할 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_ingest_bootstrap.sh`
  - `PYTHONPATH=/Users/woody/ai/stockanalysis/src python3 -m stockanalysis.ingest.cli list-sources`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task ingest-bootstrap`

## Deliverables

- 필수 결과물:
  - `pyproject.toml`
  - `src/stockanalysis/ingest/`
  - `tests/`
  - `docs/ingest-bootstrap.md`
  - `scripts/verify_ingest_bootstrap.sh`
  - `docs/tasks/ingest-bootstrap/handoff.md`
- 선택 결과물:
  - source seed alignment update

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다

작업 전용 체크를 아래에 추가한다.

- [x] collector 계층과 seed/reference 계층이 분리되어 있다
- [x] SEC/FRED/Alpha Vantage request builder가 존재한다
- [x] 기본 CLI와 테스트 경로가 존재한다

## Verification Plan

- 자동 검증:
  - `bash scripts/verify_ingest_bootstrap.sh`
  - `awh verify --task ingest-bootstrap`
  - placeholder 검색
- 수동 검증:
  - `docs/ingest-bootstrap.md`가 seed와 collector의 역할을 분리해서 설명하는지 확인
- 브라우저, 로그, metric 검증:
  - 없음. bootstrap 단계에서는 dry-run request builder와 local test를 우선한다
- 어떤 증거가 있어야 완료로 간주하는가:
  - CLI/테스트가 통과한다
  - task readiness가 통과한다
  - 초기 소스 선택과 근거가 문서로 남아 있다

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: live fetch 경로는 유지하되, 문제가 되는 source adapter를 일시적으로 registry에서 제외하고 dry-run builder만 남긴다.

## Open Questions

- 질문: 첫 실제 ingest 구현을 SEC, FRED, Alpha Vantage 중 어디부터 시작할지
- 답이 없을 때 적용할 임시 가정: key 없이도 시작 가능한 SEC와, 구조가 단순한 FRED를 먼저 구현 대상으로 삼는다.

- 질문: market data provider를 bootstrap 이후에도 Alpha Vantage로 유지할지
- 답이 없을 때 적용할 임시 가정: bootstrap 단계에서는 유지하되, scale 단계에서 재평가한다.
