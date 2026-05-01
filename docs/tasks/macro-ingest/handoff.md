# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: macro-ingest
- 담당: Codex
- 날짜: 2026-04-18

## Current Status

- 완료:
  - `macro-ingest` task를 scaffold했다.
  - `src/stockanalysis/ingest/macro/` 아래에 series spec, defaults, FRED normalizer, SQL renderer를 추가했다.
  - CLI에 `macro-default-series`, `macro-sync` 명령을 추가했다.
  - FRED fixture와 unit test, verification script, 설계 문서를 추가했다.
  - `bash scripts/verify_macro_ingest.sh`가 통과했다.
  - task readiness 검증과 placeholder 검증을 통과했다.
- 진행 중:
  - 없음.
- 막힌 점:
  - 없음. live fetch smoke는 API key가 있을 때만 추가 검증 가능하다.

## Files Touched

- 생성:
  - `docs/macro-ingest.md`
  - `scripts/verify_macro_ingest.sh`
  - `src/stockanalysis/ingest/macro/__init__.py`
  - `src/stockanalysis/ingest/macro/models.py`
  - `src/stockanalysis/ingest/macro/defaults.py`
  - `src/stockanalysis/ingest/macro/fred.py`
  - `src/stockanalysis/ingest/macro/sql.py`
  - `tests/fixtures/fred_series_CPIAUCSL.json`
  - `tests/fixtures/fred_observations_CPIAUCSL.json`
  - `tests/test_macro_ingest.py`
  - `docs/tasks/macro-ingest/contract.md`
  - `docs/tasks/macro-ingest/plan.md`
  - `docs/tasks/macro-ingest/handoff.md`
  - `docs/tasks/macro-ingest/review.md`
- 수정:
  - `README.md`
  - `docs/ingest-bootstrap.md`
  - `docs/verification-plan.md`
  - `docs/tasks/ingest-bootstrap/handoff.md`
  - `src/stockanalysis/ingest/cli.py`
- 의도적으로 안 건드린 것:
  - DDL migration
  - seed SQL
  - direct DB execute 계층
  - scheduler/backfill state

## Decisions

- 결정:
  - 첫 실제 ingest 대상은 `macro`로 고정한다.
  - 기본 거시 series는 8개 bootstrap 세트로 시작한다.
  - missing observation 값 `.` 는 skip한다.
  - 현재 단계는 direct DB write 대신 SQL upsert 생성까지 구현한다.
  - fixture 기반 검증을 canonical 자동 검증 경로로 사용한다.
- 이유:
  - 종목 유니버스 매핑 없이도 시장 레짐과 사이클 입력으로 바로 연결할 수 있다.
  - live API 의존성을 제거해야 deterministic한 CI/로컬 검증이 가능하다.
  - revision/vintage 복잡도는 다음 단계로 미루는 편이 현재 범위에 맞다.

## Verification Already Run

- 명령: `/tmp/agent-work-harness/scripts/new-task.sh backend /Users/woody/ai/stockanalysis macro-ingest --with-plan`
- 관찰한 결과: task scaffold가 생성되었다.

- 명령: `bash -n /Users/woody/ai/stockanalysis/scripts/verify_macro_ingest.sh`
- 관찰한 결과: shell syntax 검사가 통과했다.

- 명령: `bash /Users/woody/ai/stockanalysis/scripts/verify_macro_ingest.sh`
- 관찰한 결과:
  - `compileall`, 전체 unittest, `macro-default-series`, fixture 기반 `macro-sync`가 모두 성공했다.
  - unit test 14개가 모두 통과했다.
  - SQL output 파일이 비어 있지 않음을 확인했다.

- 명령: `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task macro-ingest`
- 관찰한 결과: `Task macro-ingest passed readiness checks.`

- 명령: `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 관찰한 결과: 출력이 없었다.

## Still Unverified

- 항목: 실제 FRED live fetch smoke
- 왜 중요한가: 현재 검증은 fixture 중심이라, API key를 넣은 실제 요청은 별도 후속 검증이 필요하다.

## Exact Next Step

- 다음 세션은 이것부터 시작: 바로 다음 task인 `macro-upsert-runner`에서 SQL 출력 결과를 canonical Postgres에 실행하는 경로를 추가한다.

## Risks

- 위험:
  - FRED 관측치의 revision/vintage를 아직 다루지 않는다.
  - 현재 SQL renderer는 `released_at`, `source_run_id`를 비워 둔다.
  - 기본 series 범위가 시장 레짐 판단에 충분하지 않을 수 있다.
- 대응:
  - revision/vintage는 별도 후속 task로 분리한다.
  - direct execute와 pipeline run 연결은 다음 task에서 추가한다.
  - bootstrap 세트는 문서화해 두고 후속 확장 task에서 넓힌다.

## Useful Context

- 파일:
  - `docs/macro-ingest.md`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/macro/fred.py`
  - `src/stockanalysis/ingest/macro/sql.py`
  - `tests/test_macro_ingest.py`
  - `scripts/verify_macro_ingest.sh`
- 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_macro_ingest.sh`
  - `PYTHONPATH=/Users/woody/ai/stockanalysis/src python3 -m stockanalysis.ingest.cli macro-default-series`
  - `PYTHONPATH=/Users/woody/ai/stockanalysis/src python3 -m stockanalysis.ingest.cli macro-sync --series-id CPIAUCSL --series-json tests/fixtures/fred_series_CPIAUCSL.json --observations-json tests/fixtures/fred_observations_CPIAUCSL.json --sql-output /tmp/stockanalysis-macro-sync.sql`
- 다시 찾기 싫은 배경지식:
  - 현재 검증 기준은 live fetch가 아니라 fixture 기반 deterministic sync다.
  - direct DB write는 의도적으로 다음 task로 미뤘다.
