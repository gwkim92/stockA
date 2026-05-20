# Task Contract

## Task

- 이름: operating-data-orchestrator
- 요청: 수동 EC2 보정이나 화면별 예외 처리 없이, 실제 운영 데이터가 한 번의 backend runner로 일관되게 채워지도록 근본 구조를 만든다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `stockanalysis-operations operating-data-run`이 기본 preview로 안전하게 운영 데이터 런 순서를 보여주고, 명시적 `--execute`일 때만 repo-outside env와 artifact 경계 안에서 가격 보강, 신호/추천, 포트폴리오 스냅샷/검토, 성과 readiness, paper validation을 순서대로 실행한다.

## Why

- 기존 `manual-local-ingest-smoke`와 worker는 market/news/AI 수집까지만 정렬했다.
- 실제 화면 오류의 근본 원인은 TSLA 같은 보유 종목 가격, 포트폴리오 스냅샷, 추천/thesis/review 파생 row, 성과 readiness를 사람이 수동으로 순서 맞춰 실행해야 했다는 점이다.
- 이 순서를 backend CLI/service boundary에 넣어야 같은 문제가 재발해도 “수동 명령 조합”이 아니라 하나의 재현 가능한 운영 런으로 복구할 수 있다.

## Scope

- 포함:
  - operating-data orchestrator service
  - `stockanalysis-operations operating-data-run` CLI
  - repo-outside generated watchlist/position CSV
  - artifact runner delegation and secret-free summary
  - data-health `portfolio-attribution-monthly` not-due semantics
  - focused tests, verify script, docs
- 제외:
  - scheduler 실제 배포/설치
  - Mac LaunchAgents/`launchctl` actual mutation
  - DB schema 변경
  - recommendation scoring formula 변경
  - paid provider 도입
  - live broker submission, kill-switch unlock, real order placement

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_operating_data_orchestrator.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_frontend_live_adapter.py`
  - `scripts/verify_operating_data_orchestrator.sh`
  - task docs, roadmap docs
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations
  - benchmark/evaluation split
  - scoring formula
  - host scheduler install files

## Boundaries

- 기본 실행은 no-write preview다.
- 실제 provider/DB write는 `--execute`가 있을 때만 허용한다.
- env file, output report, generated CSV, artifact root는 repo 밖이어야 한다.
- artifact runner를 통해 stdout/stderr/metadata를 남긴다.
- paper validation은 audit-only다. 브로커 제출, kill switch 해제, 실거래 주문은 하지 않는다.
- public report에는 DB URL, API key, token, bearer 값이 절대 들어가면 안 된다.

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src python3 -m unittest tests.test_operating_data_orchestrator tests.test_data_operations_cli tests.test_frontend_live_adapter`
  - `PYTHONPATH=src python3 -m compileall src tests`
  - `bash scripts/verify_operating_data_orchestrator.sh`
  - `git diff --check`

## Done Criteria

- [x] Preview mode produces the full operating-data step order without executing commands.
- [x] Execute mode delegates every write step through the artifact runner.
- [x] Missing event/portfolio symbols are detected before signal generation.
- [x] Generated CSV inputs are repo-outside and secret-free.
- [x] `/api/data-health` does not mark attribution as missing before any outcome is due.
- [x] Verification evidence is recorded in handoff.
