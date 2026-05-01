# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: macro-ingest
- 요청: 첫 실제 적재 경로로 FRED 기반 거시지표를 정규화하고, `macro.series`와 `macro.observation`에 적재 가능한 SQL upsert 출력까지 연결한다.
- 담당: Codex
- 날짜: 2026-04-18

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 기본 거시 series 목록, FRED payload 정규화, fixture 기반 deterministic 검증, SQL upsert 생성, CLI entrypoint가 모두 동작하며 다음 단계에서 DB execute runner를 바로 붙일 수 있다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: 거시지표는 종목 유니버스 매핑 없이 시장 레짐과 테마 사이클 입력으로 곧바로 쓸 수 있어서, 첫 실제 ingest 흐름으로 가장 안전하고 가치가 높다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/config.py`
  - `src/stockanalysis/ingest/registry.py`
  - `src/stockanalysis/ingest/sources/fred.py`
  - `db/migrations/0002_priority_1_tables.sql`
- 관련 문서:
  - `docs/ingest-bootstrap.md`
  - `docs/db-schema-design.md`
  - `docs/verification-plan.md`
  - `docs/tasks/ingest-bootstrap/handoff.md`
- 이전 결정:
  - 첫 실제 ingest는 `macro`부터 시작한다.
  - `FRED`를 초기 거시 데이터 source로 사용한다.
  - 현재 단계는 direct DB write보다 정규화와 검증 가능한 출력 형식을 먼저 고정한다.

## Scope

- 포함:
  - 기본 FRED macro series 목록 정의
  - FRED metadata/observations payload 정규화
  - fixture 기반 macro sync 테스트
  - `macro.series`, `macro.observation` upsert SQL 생성
  - CLI에서 macro sync 실행 경로 추가
  - task 문서와 verification 문서 갱신
- 제외:
  - Postgres direct execute
  - scheduler/backfill state 저장
  - ALFRED vintage/revision ingestion
  - 추가 macro series 대량 확장
  - 다른 source 연동

## Mutable Surface

여러 경로가 있으면 값은 다음 줄 bullet list로 적어도 된다.

- 수정 가능한 파일:
  - `README.md`
  - `docs/macro-ingest.md`
  - `docs/verification-plan.md`
  - `docs/tasks/macro-ingest/contract.md`
  - `docs/tasks/macro-ingest/plan.md`
  - `docs/tasks/macro-ingest/handoff.md`
  - `docs/tasks/macro-ingest/review.md`
  - `docs/tasks/ingest-bootstrap/handoff.md`
  - `scripts/verify_macro_ingest.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/macro/`
  - `tests/test_macro_ingest.py`
  - `tests/fixtures/fred_series_CPIAUCSL.json`
  - `tests/fixtures/fred_observations_CPIAUCSL.json`
- 수정 금지 파일:
  - 기존 DDL migration
  - seed SQL
  - 외부 하네스 원본 저장소(`/tmp/agent-work-harness`) 내부 파일
- 검증에 사용할 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_macro_ingest.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task macro-ingest`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`

## Deliverables

- 필수 결과물:
  - `docs/macro-ingest.md`
  - `src/stockanalysis/ingest/macro/`
  - `tests/test_macro_ingest.py`
  - `scripts/verify_macro_ingest.sh`
  - `docs/tasks/macro-ingest/contract.md`
  - `docs/tasks/macro-ingest/plan.md`
  - `docs/tasks/macro-ingest/handoff.md`
- 선택 결과물:
  - `docs/tasks/macro-ingest/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다

작업 전용 체크를 아래에 추가한다.

- [x] fixture 기반 macro sync가 deterministic하게 검증된다
- [x] `macro.series`와 `macro.observation` upsert SQL이 생성된다
- [x] live fetch 없이도 CLI smoke test가 가능하다

## Verification Plan

- 자동 검증: `bash /Users/woody/ai/stockanalysis/scripts/verify_macro_ingest.sh`, `awh verify --task macro-ingest`, placeholder 검색
- 수동 검증: `docs/macro-ingest.md`가 왜 macro를 첫 ingest로 잡았는지와 현재 구현 경계를 명확히 설명하는지 검토
- 브라우저, 로그, metric 검증: 현재는 CLI/테스트 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: unit test 14개 통과, fixture 기반 `macro-sync`가 SQL 파일을 생성, task readiness 검증 통과, placeholder가 없다

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: live fetch 경로를 일시적으로 비활성화하지 않고도 fixture 기반 경로만 유지할 수 있다. SQL 생성 로직에 문제가 있으면 `macro-sync`를 summary 출력 전용으로 축소한다.

## Open Questions

- 질문: `macro-sync`가 바로 DB execute까지 책임질지, 별도 runner에서 SQL/DB 둘 다 지원할지
- 답이 없을 때 적용할 임시 가정: 현재는 정규화와 SQL 생성까지만 책임지고, direct execute는 다음 task에서 분리한다.

- 질문: 초기 기본 macro series를 얼마나 넓게 잡을지
- 답이 없을 때 적용할 임시 가정: 시장 레짐 판단에 필요한 최소 bootstrap 세트만 유지하고, 이후 `macro-series-expansion`에서 확장한다.
