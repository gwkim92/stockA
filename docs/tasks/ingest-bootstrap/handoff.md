# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: ingest-bootstrap
- 담당: Codex
- 날짜: 2026-04-18

## Current Status

- 완료:
  - `ingest-bootstrap` task를 scaffold했다.
  - ingest package, source adapters, CLI, tests, verification script를 추가했다.
  - `docs/ingest-bootstrap.md`에 초기 source 선택과 collector 구조를 정리했다.
  - `db/seeds/0002_data_sources_seed.sql`를 현재 source 선택과 맞추도록 갱신했다.
  - ingest bootstrap 검증, seed 재검증, task readiness 검증을 통과했다.
  - 후속 task로 `macro-ingest`를 시작할 수 있는 구조를 열었다.
- 진행 중:
  - 다음 단계 task로 `macro-ingest`가 진행 중이다.
- 막힌 점:
  - 없음. 다만 실제 live fetch는 API key 또는 identified User-Agent가 필요하다.

## Files Touched

- 생성:
  - `pyproject.toml`
  - `.env.example`
  - `docs/ingest-bootstrap.md`
  - `scripts/verify_ingest_bootstrap.sh`
  - `src/stockanalysis/__init__.py`
  - `src/stockanalysis/ingest/__init__.py`
  - `src/stockanalysis/ingest/config.py`
  - `src/stockanalysis/ingest/models.py`
  - `src/stockanalysis/ingest/http.py`
  - `src/stockanalysis/ingest/registry.py`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/sources/base.py`
  - `src/stockanalysis/ingest/sources/sec.py`
  - `src/stockanalysis/ingest/sources/fred.py`
  - `src/stockanalysis/ingest/sources/alpha_vantage.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_ingest_sources.py`
  - `docs/tasks/ingest-bootstrap/contract.md`
  - `docs/tasks/ingest-bootstrap/plan.md`
  - `docs/tasks/ingest-bootstrap/handoff.md`
  - `docs/tasks/ingest-bootstrap/review.md`
- 수정:
  - `README.md`
  - `docs/verification-plan.md`
  - `docs/tasks/seed-bootstrap/handoff.md`
  - `db/seeds/0002_data_sources_seed.sql`
- 의도적으로 안 건드린 것:
  - DB write/upsert 계층
  - scheduler
  - universe bootstrap
  - news ingestion

## Decisions

- 결정:
  - bootstrap collector는 SEC, FRED, Alpha Vantage 3개 source adapter로 시작한다.
  - adapter는 request builder와 execution entrypoint까지만 구현한다.
  - source credentials는 env var로 읽고, dry-run build-request는 placeholder를 허용한다.
  - `stooq` seed는 제거하고 `alpha_vantage` seed로 맞춘다.
- 이유:
  - 현재 목표는 실제 적재기 구조를 여는 것이지, 바로 full ETL을 완성하는 것이 아니다.
  - official documentation을 확인 가능한 source 중심으로 좁히는 편이 안전하다.

## Verification Already Run

- 명령: `/tmp/agent-work-harness/scripts/new-task.sh backend /Users/woody/ai/stockanalysis ingest-bootstrap --with-plan`
- 관찰한 결과: task scaffold가 생성되었다.

- 명령: `bash /Users/woody/ai/stockanalysis/scripts/verify_ingest_bootstrap.sh`
- 관찰한 결과:
  - `compileall`, `unittest`, `list-sources`, `build-request` dry-run이 모두 성공했다.
  - unit test 8개가 모두 통과했다.

- 명령: `bash /Users/woody/ai/stockanalysis/scripts/verify_seed_bootstrap.sh`
- 관찰한 결과:
  - migration 3개와 seed 2개가 순서대로 적용되었다.
  - row count는 `ref.market=1`, `ref.exchange=3`, `ingest.data_source=6`으로 출력되었다.

- 명령: `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task ingest-bootstrap`
- 관찰한 결과: `Task ingest-bootstrap passed readiness checks.`

- 명령: `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 관찰한 결과: placeholder 출력이 없었다.

## Still Unverified

- 항목: 실제 live fetch smoke
- 왜 중요한가: 현재 기본 검증은 dry-run/로컬 테스트 중심이라, 실 API 환경변수 세팅 후 한 번 더 확인해야 한다.

- 항목: DB upsert 연결
- 왜 중요한가: 현재 collector는 request/fetch 계층까지만 있고, canonical schema 적재는 아직 후속 task다.

## Exact Next Step

- 다음 세션은 이것부터 시작: `docs/tasks/macro-ingest/`와 `src/stockanalysis/ingest/macro/`를 읽고, FRED macro 정규화와 SQL upsert 출력 경로를 구현한다.

## Risks

- 위험:
  - Alpha Vantage는 bootstrap 용도로는 쓸 수 있지만 장기 scale source로는 재평가가 필요할 수 있다.
  - 실제 live fetch는 credentials와 fair access 헤더가 필요하다.
- 대응:
  - source selection을 문서에 명시하고, bootstrap 선택임을 분리해서 적었다.
  - dry-run request builder가 credentials 없이도 동작하도록 했다.

## Useful Context

- 파일:
  - `docs/ingest-bootstrap.md`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/registry.py`
  - `db/seeds/0002_data_sources_seed.sql`
  - `tests/test_ingest_cli.py`
  - `tests/test_ingest_sources.py`
- 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_ingest_bootstrap.sh`
  - `PYTHONPATH=/Users/woody/ai/stockanalysis/src python3 -m stockanalysis.ingest.cli list-sources`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task ingest-bootstrap`
- 다시 찾기 싫은 배경지식:
  - seed는 기준정보, collector는 실제 데이터 수집 계층이다.
  - SEC/FRED/Alpha Vantage 선택 근거는 공식 문서 기준 bootstrap 판단이다.
