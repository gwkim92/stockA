# Task Contract

## Task

- 이름: portfolio-risk-budget-guardrail-run
- 요청: 기존 포트폴리오 위험 예산 화면을 운영 판단에 남는 backend guardrail runner로 확장한다.
- 담당: Codex
- 날짜: 2026-05-26

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `stockanalysis-operations portfolio-risk-budget-guardrail-run --portfolio-name ... --as-of-date YYYY-MM-DD --execute`가 최신 `portfolio.position_snapshot`과 classification exposure를 읽어 단일 종목, 섹터, 테마, 미분류, benchmark drift 준비 상태를 평가하고, `ops.pipeline_run`과 `ai.eval_run`에 read-only 보고서를 저장한다.

## Scope

- 포함:
  - portfolio risk budget guardrail runner 추가
  - CLI 명령 추가
  - `ai.eval_run` 저장 report schema 추가
  - 단일 종목 한도, 리밸런싱 하한, 섹터/테마 집중, 미분류 노출 계산
  - benchmark composition이 없으면 drift를 만들지 않고 `insufficient_benchmark_composition`으로 명시
  - unit/CLI test와 roadmap/AWH 문서 정리
- 제외:
  - 신규 DB migration
  - 추천 score/weight 변경
  - paper validation 기존 판단식 변경
  - 자동 리밸런싱/주문 실행
  - broker credential, live order submit, kill switch unlock
  - repo 안 secret/env 값

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/portfolio_risk_budget_guardrail.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_portfolio_risk_budget_guardrail.py`
  - `tests/test_data_operations_cli.py`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/portfolio-risk-budget-guardrail-run/*`
- 수정 금지 파일:
  - 추천 scoring formula/weights
  - benchmark/evaluation split
  - broker/order submit path
  - repo 안 secret/env 값

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_portfolio_risk_budget_guardrail tests.test_data_operations_cli`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-risk-budget-guardrail-run`

## Done Criteria

- runner는 risk budget 상태를 계산하되 주문, 리밸런싱, 추천 weight를 바꾸지 않는다.
- benchmark composition이 없을 때 drift를 추정하지 않고 데이터 부족으로 표시한다.
- output은 paper validation/recommendation 앞단에서 사용할 수 있는 `risk_gate_decision`과 blocking/warning reasons를 포함한다.
- task handoff는 다음 사람이 EC2 smoke까지 이어갈 수 있게 남긴다.
