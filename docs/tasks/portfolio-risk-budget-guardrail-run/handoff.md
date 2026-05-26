# Session Handoff

## Current Status

- 완료: portfolio risk budget을 화면 DTO에서 backend guardrail report runner로 승격했고, 로컬 검증을 통과했다.

## Decisions

- 기존 `portfolio-risk-budget-policy-v2`는 이미 완료된 UI/API DTO 작업이므로 재사용하지 않는다.
- 이번 runner는 `portfolio.position_snapshot`, `portfolio.allocation_policy`, `ref.instrument_classification_membership`, `ref.classification_node`만 읽는다.
- benchmark composition 데이터가 아직 없으므로 benchmark drift를 임의 계산하지 않는다. 대신 `insufficient_benchmark_composition`으로 명시한다.
- 추천 weight, paper validation 기존 결과, broker submit은 변경하지 않는다.

## Exact Next Step

- exact next step: EC2에서 최신 코드를 pull한 뒤 `portfolio-risk-budget-guardrail-run --execute`를 실제 Postgres에 대해 1회 smoke하고 `run_id`, `eval_run_id`, `risk_gate_decision`을 기록한다.

## Implementation Notes

- 새 CLI: `stockanalysis-operations portfolio-risk-budget-guardrail-run`
- 새 runner: `src/stockanalysis/operations/portfolio_risk_budget_guardrail.py`
- 저장:
  - `ops.pipeline_run.pipeline_name='portfolio_risk_budget_guardrail'`
  - `ai.eval_run.eval_name='portfolio_risk_budget_guardrail'`
- 계산:
  - 단일 종목 상한
  - 리밸런싱 하한
  - 섹터 집중
  - 테마 집중
  - 미분류 노출
  - benchmark drift 준비 상태
- benchmark composition 데이터가 없으면 drift를 추정하지 않고 `insufficient_benchmark_composition`으로 저장한다.
- `paper_validation_input_allowed`는 risk gate가 `within_budget`일 때만 true다.
- 추천 weight, paper validation 기존 로직, 자동 주문, broker submit은 변경하지 않는다.

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_portfolio_risk_budget_guardrail tests.test_data_operations_cli`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- Passed: `git diff --check`
- Passed: `bash scripts/verify_project_execution_roadmap.sh`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-risk-budget-guardrail-run`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m stockanalysis.operations.cli portfolio-risk-budget-guardrail-run --help`
