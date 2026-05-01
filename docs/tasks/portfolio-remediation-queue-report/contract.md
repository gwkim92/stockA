# Task Contract

## Task

- 이름: portfolio-remediation-queue-report
- 요청: portfolio review attention items를 처리 가능한 remediation queue로 보여준다.
- 담당: Codex
- 날짜: 2026-04-27

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `portfolio-remediation-queue` CLI가 최근 portfolio review items 중 조치가 필요한 항목을 remediation type, suggested runner, reason과 함께 JSON으로 출력한다.

## Why

- run history는 조치 후보를 보여주지만, 운영자는 다음에 어떤 runner나 수동 검토를 실행해야 하는지 알아야 한다. 이 report는 `needs_thesis_review`, `needs_outcome_review`, `needs_weight_review` 같은 action을 처리 큐로 분류한다.

## Scope

- 포함:
  - read-only remediation queue SQL
  - action to remediation type mapping
  - suggested runner/next step metadata
  - CLI report
  - unit tests and Docker integration verification
  - docs/task handoff 갱신
- 제외:
  - DB schema 변경
  - queue table 저장
  - remediation 자동 실행
  - 실거래 주문/체결
  - LLM 기반 판단

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/plans/2026-04-27-portfolio-remediation-queue-report.md`
  - `docs/portfolio-remediation-queue-report.md`
  - `docs/portfolio-review-run-history-report.md`
  - `docs/tasks/portfolio-remediation-queue-report/`
  - `docs/verification-plan.md`
  - `scripts/verify_portfolio_remediation_queue_report.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/signal/portfolio_remediation_queue.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_portfolio_remediation_queue.py`
- 수정 금지 파일:
  - DB migrations
  - portfolio review action rule
  - attribution calculation
  - recommendation score formula
  - thesis generation rule
- 검증에 사용할 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n scripts/verify_portfolio_remediation_queue_report.sh`
  - `bash scripts/verify_portfolio_remediation_queue_report.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-queue-report`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - `portfolio-remediation-queue` CLI
  - queue report module
  - queue unit tests
  - Docker verify script
  - queue docs
  - task contract/plan/handoff/review

## Completion Criteria

- [x] queue report가 조치 필요 item만 반환한다.
- [x] action별 remediation type과 suggested runner를 반환한다.
- [x] CLI가 JSON report를 출력한다.
- [x] Docker verify가 BABA `needs_thesis_review`를 `thesis_remediation` queue item으로 확인한다.
- [x] docs와 handoff가 갱신된다.
- [x] 하네스 검증이 통과한다.

## Risks

- queue는 read-only report이므로 실제 remediation 상태를 저장하지 않는다.
- suggested runner는 운영 힌트이며 자동 실행 보장이 아니다.
- position snapshot에 thesis가 없으면 recommendation에 thesis가 있어도 thesis remediation으로 분류한다.
