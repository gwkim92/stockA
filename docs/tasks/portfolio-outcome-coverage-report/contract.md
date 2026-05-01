# Task Contract

## Task

- 이름: portfolio-outcome-coverage-report
- 요청: portfolio attribution에서 제외되는 outcome 없는 position을 보고한다.
- 담당: Codex
- 날짜: 2026-04-27

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `portfolio-outcome-coverage-report` CLI가 portfolio snapshot 전체를 읽고 covered, missing outcome, missing thesis, missing weight position과 weight coverage를 JSON으로 출력한다.

## Why

- attribution v1은 outcome이 없는 position을 계산에서 제외한다. 제외된 position을 별도 보고하지 않으면 보유 검토가 잘 되고 있는지 판단할 때 coverage blind spot이 생긴다.

## Scope

- 포함:
  - read-only coverage lookup SQL
  - coverage summary builder
  - CLI report
  - fixture with covered and missing thesis positions
  - unit tests and Docker integration verification
  - docs/task handoff 갱신
- 제외:
  - DB schema 변경
  - portfolio attribution methodology 변경
  - outcome 자동 생성
  - thesis 자동 생성
  - 실거래 PnL
  - LLM 기반 판단

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/plans/2026-04-27-portfolio-outcome-coverage-report.md`
  - `docs/portfolio-attribution-bootstrap.md`
  - `docs/portfolio-outcome-coverage-report.md`
  - `docs/tasks/portfolio-outcome-coverage-report/`
  - `docs/verification-plan.md`
  - `scripts/verify_portfolio_outcome_coverage_report.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/performance/coverage.py`
  - `tests/fixtures/portfolio_positions_long_term_paper_with_gap.csv`
  - `tests/test_ingest_cli.py`
  - `tests/test_portfolio_outcome_coverage_report.py`
- 수정 금지 파일:
  - performance attribution calculation
  - recommendation score formula
  - thesis generation rule
  - DB migrations
- 검증에 사용할 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n scripts/verify_portfolio_outcome_coverage_report.sh`
  - `bash scripts/verify_portfolio_outcome_coverage_report.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-outcome-coverage-report`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - `portfolio-outcome-coverage-report` CLI
  - coverage report module
  - coverage unit tests
  - Docker verify script
  - coverage docs
  - task contract/plan/handoff/review

## Completion Criteria

- [x] coverage row가 covered/missing outcome/missing thesis/missing weight를 구분한다.
- [x] coverage summary가 count, weight, cash weight, coverage ratios를 반환한다.
- [x] CLI가 JSON report를 출력한다.
- [x] Docker verify가 AAPL covered, BABA missing thesis를 확인한다.
- [x] docs와 handoff가 갱신된다.
- [x] 하네스 검증이 통과한다.

## Verification Plan

- 자동 검증: compileall, unittest, shell syntax, Docker integration verify, harness verify, placeholder 검색
- 수동 검증: `docs/portfolio-outcome-coverage-report.md`에서 attribution 제외 원인과 read-only boundary가 명확한지 확인
- 어떤 증거가 있어야 완료로 간주하는가: Docker Postgres에서 coverage report가 AAPL covered 1건, BABA missing thesis 1건, covered weight `0.0500`, missing thesis weight `0.0300`, cash weight `0.9200`을 확인한다.

## Risks

- missing thesis position은 thesis/outcome 생성 작업 없이는 attribution 대상이 아니다.
- weight가 null이면 cash weight는 정확히 계산할 수 없다.
- 이 report는 자동 remediation이 아니라 blind spot 관찰용이다.
