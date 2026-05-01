# Task Contract

## Task

- 이름: portfolio-remediation-ticket-bootstrap
- 요청: portfolio remediation queue item을 persistent 운영 ticket으로 저장한다.
- 담당: Codex
- 날짜: 2026-04-28

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `portfolio-remediation-ticket-bootstrap` CLI가 조치 필요 review item을 `portfolio.remediation_ticket`에 upsert하고, 중복 실행해도 동일 ticket이 중복 생성되지 않는다.

## Why

- read-only queue는 현재 조치 후보만 보여준다. 운영 시스템은 어떤 remediation이 아직 열려 있는지, 언제 마지막으로 관측됐는지, 어떤 runner로 처리해야 하는지 상태를 저장해야 한다.

## Scope

- 포함:
  - `portfolio.remediation_ticket` migration
  - queue action to remediation ticket upsert
  - ticket bootstrap CLI
  - unit tests and Docker integration verification
  - docs/task handoff 갱신
- 제외:
  - remediation 자동 실행
  - ticket resolve/ignore UI 또는 command
  - 실거래 주문/체결
  - review action rule 변경
  - recommendation/thesis/attribution 산식 변경
  - LLM 기반 판단

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `db/migrations/0012_portfolio_remediation_ticket.sql`
  - `docs/plans/2026-04-28-portfolio-remediation-ticket-bootstrap.md`
  - `docs/db-schema-design.md`
  - `docs/portfolio-remediation-ticket-bootstrap.md`
  - `docs/portfolio-remediation-queue-report.md`
  - `docs/tasks/portfolio-remediation-ticket-bootstrap/`
  - `docs/verification-plan.md`
  - `scripts/verify_portfolio_remediation_ticket_bootstrap.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/signal/portfolio_remediation_ticket.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_portfolio_remediation_ticket.py`
- 수정 금지 파일:
  - portfolio review action rule
  - attribution calculation
  - recommendation score formula
  - thesis generation rule
  - performance outcome calculation
- 검증에 사용할 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n scripts/verify_portfolio_remediation_ticket_bootstrap.sh`
  - `bash scripts/verify_portfolio_remediation_ticket_bootstrap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-ticket-bootstrap`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - `portfolio.remediation_ticket` table
  - `portfolio-remediation-ticket-bootstrap` CLI
  - ticket bootstrap module
  - ticket unit tests
  - Docker verify script
  - ticket docs
  - task contract/plan/handoff/review

## Completion Criteria

- [x] migration이 실제 Postgres에 적용된다.
- [x] bootstrap이 queue item을 ticket으로 upsert한다.
- [x] 중복 bootstrap 실행이 duplicate ticket을 만들지 않는다.
- [x] CLI가 JSON summary를 출력한다.
- [x] Docker verify가 BABA `needs_thesis_review` ticket을 확인한다.
- [x] docs와 handoff가 갱신된다.
- [x] 하네스 검증이 통과한다.

## Risks

- ticket은 상태 저장만 하며 실제 remediation을 수행하지 않는다.
- `resolved`, `ignored` 같은 lifecycle command는 아직 없다.
- review rerun으로 review item id가 바뀌므로 ticket은 `review_item_id` FK를 갖지 않는다.
