# Task Contract

## Task

- 이름: portfolio-remediation-ticket-report
- 요청: persistent remediation ticket을 운영자가 상태별로 조회할 수 있게 한다.
- 담당: Codex
- 날짜: 2026-04-28

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `portfolio-remediation-ticket-report` CLI가 `portfolio.remediation_ticket`을 read-only JSON으로 조회하고, status/action/remediation type/suggested runner filter를 지원한다.

## Why

- ticket bootstrap은 조치 필요 항목을 저장하지만, 운영자는 현재 열려 있는 ticket과 처리 상태를 빠르게 확인할 수 있어야 한다. 이 report는 다음 remediation 작업 우선순위를 확인하는 운영 화면의 API 전 단계다.

## Scope

- 포함:
  - read-only ticket report SQL
  - CLI report
  - unit tests and Docker integration verification
  - docs/task handoff 갱신
- 제외:
  - DB schema 변경
  - remediation 자동 실행
  - ticket resolve/ignore command
  - 실거래 주문/체결
  - review action rule 변경
  - recommendation/thesis/attribution/performance 산식 변경
  - LLM 기반 판단

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/plans/2026-04-28-portfolio-remediation-ticket-report.md`
  - `docs/portfolio-remediation-ticket-report.md`
  - `docs/portfolio-remediation-ticket-bootstrap.md`
  - `docs/tasks/portfolio-remediation-ticket-report/`
  - `docs/verification-plan.md`
  - `scripts/verify_portfolio_remediation_ticket_report.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/signal/portfolio_remediation_ticket.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_portfolio_remediation_ticket.py`
- 수정 금지 파일:
  - DB migrations
  - portfolio review action rule
  - attribution calculation
  - recommendation score formula
  - thesis generation rule
  - performance outcome calculation
- 검증에 사용할 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n scripts/verify_portfolio_remediation_ticket_report.sh`
  - `bash scripts/verify_portfolio_remediation_ticket_report.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-ticket-report`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - `portfolio-remediation-ticket-report` CLI
  - ticket report SQL/function
  - ticket report unit tests
  - Docker verify script
  - ticket report docs
  - task contract/plan/handoff/review

## Completion Criteria

- [x] report가 ticket rows를 read-only로 반환한다.
- [x] status/action/remediation type/suggested runner filter를 지원한다.
- [x] CLI가 JSON report를 출력한다.
- [x] Docker verify가 BABA open ticket report를 확인한다.
- [x] docs와 handoff가 갱신된다.
- [x] 하네스 검증이 통과한다.

## Risks

- report는 조회만 하며 ticket 상태를 변경하지 않는다.
- open ticket의 실제 해결 여부는 후속 lifecycle command가 필요하다.
- `status all`은 전체 상태 조회용이며 기본값은 `open`이다.
