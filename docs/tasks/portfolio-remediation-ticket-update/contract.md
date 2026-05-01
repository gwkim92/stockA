# Task Contract

## Task

- 이름: portfolio-remediation-ticket-update
- 요청: persistent remediation ticket의 lifecycle status를 변경한다.
- 담당: Codex
- 날짜: 2026-04-29

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `portfolio-remediation-ticket-update` CLI가 특정 portfolio의 ticket status를 `open`, `in_progress`, `resolved`, `ignored` 중 하나로 바꾸고, resolved/ignored 상태에는 `resolved_at`을 기록한다.

## Why

- ticket report는 backlog를 보여주지만, 운영자가 처리 시작/해결/무시 상태를 반영할 수 없으면 remediation queue가 계속 누적된다. 최소 lifecycle update가 있어야 portfolio review 운영 루프가 닫힌다.

## Scope

- 포함:
  - ticket status update SQL
  - pipeline run provenance
  - CLI update command
  - unit tests and Docker integration verification
  - docs/task handoff 갱신
- 제외:
  - DB schema 변경
  - remediation 자동 실행
  - assignee, note, due date 저장
  - 실거래 주문/체결
  - review action rule 변경
  - recommendation/thesis/attribution/performance 산식 변경
  - LLM 기반 판단

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/plans/2026-04-29-portfolio-remediation-ticket-update.md`
  - `docs/portfolio-remediation-ticket-update.md`
  - `docs/portfolio-remediation-ticket-report.md`
  - `docs/tasks/portfolio-remediation-ticket-update/`
  - `docs/verification-plan.md`
  - `scripts/verify_portfolio_remediation_ticket_update.sh`
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
  - `bash -n scripts/verify_portfolio_remediation_ticket_update.sh`
  - `bash scripts/verify_portfolio_remediation_ticket_update.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-ticket-update`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - `portfolio-remediation-ticket-update` CLI
  - ticket update SQL/function
  - ticket update unit tests
  - Docker verify script
  - ticket update docs
  - task contract/plan/handoff/review

## Completion Criteria

- [x] update가 target portfolio의 ticket 1건만 변경한다.
- [x] unsupported status와 non-positive ticket id를 거부한다.
- [x] resolved/ignored는 `resolved_at`을 기록한다.
- [x] open/in_progress는 `resolved_at`을 비운다.
- [x] CLI가 JSON summary를 출력한다.
- [x] Docker verify가 BABA ticket resolved lifecycle을 확인한다.
- [x] docs와 handoff가 갱신된다.
- [x] 하네스 검증이 통과한다.

## Risks

- assignee/note/due date는 아직 저장하지 않는다.
- status update는 실제 remediation 수행을 의미하지 않는다.
- update provenance는 `ops.pipeline_run`에는 남지만 ticket row에는 별도 status run id로 저장하지 않는다.
