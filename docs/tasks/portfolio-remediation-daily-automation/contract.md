# Task Contract

## Task

- 이름: portfolio-remediation-daily-automation
- 요청: daily portfolio remediation 운영 runner를 추가한다.
- 담당: Codex
- 날짜: 2026-04-30

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `portfolio-remediation-daily-run` CLI가 portfolio review bootstrap, remediation ticket bootstrap, open ticket report를 순서대로 실행하고 하나의 JSON summary로 운영 결과를 반환한다.

## Why

- 현재는 review, ticket 생성, ticket 조회가 모두 개별 명령이다. 반복 운영에서는 같은 순서를 매번 정확히 실행해야 하므로, 검증된 하위 runner를 묶는 deterministic daily runner가 필요하다.

## Scope

- 포함:
  - daily runner module
  - top-level pipeline run provenance
  - CLI command
  - unit tests and Docker integration verification
  - automation loop contract
  - docs/task handoff 갱신
- 제외:
  - 실제 OS cron, hosted automation, app automation 활성화
  - remediation 자동 실행
  - ticket auto resolve/ignore
  - DB schema 변경
  - 실거래 주문/체결
  - review action rule 변경
  - recommendation/thesis/attribution/performance 산식 변경
  - LLM 기반 판단

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/plans/2026-04-30-portfolio-remediation-daily-automation.md`
  - `docs/portfolio-remediation-daily-automation.md`
  - `docs/portfolio-remediation-ticket-update.md`
  - `docs/tasks/portfolio-remediation-daily-automation/`
  - `docs/verification-plan.md`
  - `scripts/verify_portfolio_remediation_daily_automation.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/signal/portfolio_remediation_daily.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_portfolio_remediation_daily.py`
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
  - `bash -n scripts/verify_portfolio_remediation_daily_automation.sh`
  - `bash scripts/verify_portfolio_remediation_daily_automation.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-daily-automation`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - `portfolio-remediation-daily-run` CLI
  - daily runner module
  - daily runner unit tests
  - Docker verify script
  - daily automation docs
  - task contract/plan/handoff/review/loop contract

## Completion Criteria

- [x] daily runner가 review bootstrap을 먼저 실행한다.
- [x] daily runner가 remediation ticket bootstrap을 다음에 실행한다.
- [x] daily runner가 open ticket report를 마지막에 실행한다.
- [x] top-level pipeline run이 succeeded/failed provenance를 남긴다.
- [x] CLI가 JSON summary를 출력한다.
- [x] Docker verify가 BABA open remediation ticket을 daily summary에서 확인한다.
- [x] docs와 handoff가 갱신된다.
- [x] 하네스 검증이 통과한다.

## Risks

- 이 작업은 실제 스케줄러를 켜지 않는다.
- open ticket이 있다고 해서 remediation이 실행된 것은 아니다.
- ticket status update는 운영자의 별도 action으로 남는다.
