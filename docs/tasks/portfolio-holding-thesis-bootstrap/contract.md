# Task Contract

## Task

- 이름: portfolio-holding-thesis-bootstrap
- 요청: 보유 포지션이 있지만 active thesis가 없어 `/portfolio/coverage`에서 `missing_thesis`로 남는 문제를 백엔드 runner로 해소한다.
- 담당: Codex
- 날짜: 2026-05-21

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 최신 포트폴리오 보유 종목 중 `linked_thesis_id`가 없는 행은 보수적 active thesis를 새로 만들거나 기존 active thesis를 재사용해 연결된다.
  - 이 처리는 `stockanalysis-ingest` CLI와 operating-data decision-daily profile에서 자동 실행 가능하다.

## Scope

- 포함:
  - 최신 포트폴리오 포지션 스냅샷에서 `linked_thesis_id`가 없는 보유 종목 조회
  - 기존 active thesis 재사용
  - 테마 멤버십, cycle snapshot, 최신 추천 상태를 이용한 보수적 보유 검토 thesis 생성
  - position snapshot `linked_thesis_id` 연결
  - `stockanalysis-ingest portfolio-holding-thesis-bootstrap` CLI 추가
  - operating data orchestrator step 추가
  - 단위/CLI/orchestrator 테스트 추가
- 제외:
  - AI가 thesis를 직접 작성하는 변경
  - 실거래, broker order, 계좌 권한
  - 기존 추천 산식이나 benchmark 기준 변경
  - performance outcome 생성 로직 변경
  - 가격 feature와 macro flow evidence 직접 재집계. 해당 신호는 기존 cycle/recommendation 계층에서 반영한다.

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/signal/portfolio_holding_thesis.py`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `tests/test_portfolio_holding_thesis_bootstrap.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_operating_data_orchestrator.py`
  - `docs/tasks/portfolio-holding-thesis-bootstrap/*`
- 수정 금지 파일:
  - `.env` secret values
  - broker/live order submission
  - benchmark/evaluation split
  - DB migrations/schema

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_portfolio_holding_thesis_bootstrap tests.test_ingest_cli tests.test_operating_data_orchestrator`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-holding-thesis-bootstrap`

## Done Criteria

- [ ] Runner 재실행이 중복 thesis를 만들지 않는다.
- [ ] 보유 포지션이 active thesis를 갖게 되면 최신 position snapshot에 연결된다.
- [ ] 포지션에 추천이 없어도 보수적 보유 검토 thesis가 생성된다.
- [ ] `stockanalysis-ingest portfolio-holding-thesis-bootstrap ...` CLI가 동작한다.
- [ ] operating data orchestrator가 portfolio snapshot 이후 이 runner를 실행한다.
- [ ] 관련 unit tests와 AWH verify가 통과한다.
