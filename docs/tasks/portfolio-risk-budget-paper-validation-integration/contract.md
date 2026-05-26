# Task Contract

## Task

- 이름: portfolio-risk-budget-paper-validation-integration
- 요청: paper validation이 최신 portfolio risk budget guardrail report를 read-only 안전 입력으로 읽게 한다.
- 담당: Codex
- 날짜: 2026-05-26

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `paper-validation-audit-run`이 live DB 실행 시 최신 `ai.eval_run.eval_name='portfolio_risk_budget_guardrail'` 결과를 읽고, `paper_validation_input_allowed=false`이면 paper validation status를 `failed`로 유지하며 blocked reason에 risk budget 차단 사유를 기록한다.

## Scope

- 포함:
  - paper validation용 portfolio risk budget guardrail lookup SQL 추가
  - guardrail snapshot parser 추가
  - `build_paper_validation_audit_plan`에 guardrail snapshot 입력 추가
  - live `run_paper_validation_audit`에서 guardrail snapshot 조회
  - paper validation report에 guardrail 상태 노출
  - unit/CLI test와 task handoff 갱신
- 제외:
  - 신규 DB migration
  - 추천 score/weight 변경
  - paper validation run schema 변경
  - 자동 주문, broker submit, kill switch 해제
  - portfolio risk budget 산식 변경
  - repo 안 secret/env 값

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/trading/paper_validation.py`
  - `tests/test_trading_paper_validation.py`
  - `docs/tasks/portfolio-risk-budget-paper-validation-integration/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
- 수정 금지 파일:
  - 추천 scoring formula/weights
  - broker/order submit path
  - kill switch unlock logic
  - benchmark/evaluation split
  - repo 안 secret/env 값

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_trading_paper_validation tests.test_data_operations_cli`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-risk-budget-paper-validation-integration`

## Done Criteria

- paper validation은 최신 risk budget guardrail eval을 읽는다.
- risk budget이 paper validation input을 허용하지 않으면 validation은 실패 상태로 남는다.
- report에는 guardrail eval id, risk gate decision, blocker/warning이 표시된다.
- broker submit과 추천 weight는 계속 변경되지 않는다.
