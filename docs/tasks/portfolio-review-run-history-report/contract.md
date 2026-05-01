# Task Contract

## Task

- 이름: portfolio-review-run-history-report
- 요청: portfolio review/coverage 결과를 운영자가 확인할 수 있는 run history report를 만든다.
- 담당: Codex
- 날짜: 2026-04-27

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `portfolio-review-run-history` CLI가 최근 portfolio review runs, risk/action counts, attention items를 JSON으로 출력한다.

## Why

- review와 coverage gate가 저장되어도 최근 실행 상태와 조치 후보를 바로 볼 수 없으면 운영 루틴으로 쓰기 어렵다. 이 report는 “잘 투자하고 있는지 계속 검토”하기 위한 audit/readout 계층이다.

## Scope

- 포함:
  - read-only portfolio review run history SQL
  - action/risk/status summary
  - attention item list
  - CLI report
  - unit tests and Docker integration verification
  - docs/task handoff 갱신
- 제외:
  - DB schema 변경
  - review action rule 변경
  - coverage gate 변경
  - remediation 자동 실행
  - dashboard UI
  - LLM report generation

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/plans/2026-04-27-portfolio-review-run-history-report.md`
  - `docs/portfolio-review-bootstrap.md`
  - `docs/portfolio-review-run-history-report.md`
  - `docs/tasks/portfolio-review-run-history-report/`
  - `docs/verification-plan.md`
  - `scripts/verify_portfolio_review_run_history_report.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/signal/portfolio_review_report.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_portfolio_review_report.py`
- 수정 금지 파일:
  - DB migrations
  - portfolio review action rule
  - attribution calculation
  - recommendation score formula
  - thesis generation rule
- 검증에 사용할 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n scripts/verify_portfolio_review_run_history_report.sh`
  - `bash scripts/verify_portfolio_review_run_history_report.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-review-run-history-report`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - `portfolio-review-run-history` CLI
  - report module
  - report unit tests
  - Docker verify script
  - report docs
  - task contract/plan/handoff/review

## Completion Criteria

- [x] report가 portfolio review run history를 반환한다.
- [x] report가 risk/action counts를 반환한다.
- [x] report가 attention items를 반환한다.
- [x] CLI가 JSON report를 출력한다.
- [x] Docker verify가 coverage-gated review 이후 AAPL monitor, BABA needs thesis review를 report에서 확인한다.
- [x] docs와 handoff가 갱신된다.
- [x] 하네스 검증이 통과한다.

## Risks

- review item reason은 text라 coverage status를 별도 column으로 집계하지 않는다.
- report는 remediation 후보를 보여줄 뿐 자동 처리하지 않는다.
- limit가 낮으면 오래된 review run은 보이지 않는다.
