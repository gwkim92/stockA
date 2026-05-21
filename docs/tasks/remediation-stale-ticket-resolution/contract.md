# Task Contract

## Task

- 이름: remediation-stale-ticket-resolution
- 요청: 포트폴리오 검토 결과가 개선된 뒤에도 과거 open remediation ticket이 화면에 남는 문제를 해소한다.
- 담당: Codex
- 날짜: 2026-05-21

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 최신 portfolio review가 더 이상 같은 instrument/action/remediation_type 후보를 만들지 않으면 기존 open/in_progress ticket은 자동으로 `resolved` 처리된다.
  - `/remediation`과 portfolio review 후속 화면은 stale `needs_thesis_review` 티켓을 계속 보여주지 않는다.

## Scope

- 포함:
  - `portfolio_remediation_ticket_bootstrap` SQL에 stale ticket resolve CTE 추가
  - bootstrap summary에 `resolved_stale_ticket_count` 노출
  - 관련 단위 테스트 보강
  - EC2에서 remediation daily 1회 재실행 후 open ticket 상태 확인
- 제외:
  - DB schema 변경
  - manual ticket status UX 변경
  - broker/order flow
  - recommendation/review scoring 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/signal/portfolio_remediation_ticket.py`
  - `tests/test_portfolio_remediation_ticket.py`
  - `docs/tasks/remediation-stale-ticket-resolution/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations/schema
  - broker/live order submission

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_portfolio_remediation_ticket`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_portfolio_holding_thesis_bootstrap tests.test_ingest_cli tests.test_operating_data_orchestrator tests.test_portfolio_remediation_ticket`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task remediation-stale-ticket-resolution`

## Done Criteria

- [ ] Bootstrap SQL resolves stale open/in_progress tickets.
- [ ] Summary reports resolved stale ticket count.
- [ ] Unit tests cover stale resolution.
- [ ] EC2 open ticket report no longer shows stale `needs_thesis_review` for holdings whose thesis coverage was repaired.
