# Session Handoff

## Current Status

- 완료: benchmark composition CSV import runner, CLI command, unit/CLI tests, EC2 repo-outside operator upload smoke까지 확인했다.

- 구현 완료: task contract를 만들었고 benchmark composition CSV import runner, CLI command, unit/CLI tests를 추가했다. guardrail source selection은 `provider_file`, `operator_upload`, `manual_seed` 순서로 선택하도록 보강했다.

## Implementation Notes

- 새 runner: `src/stockanalysis/operations/benchmark_composition_import.py`
  - repo-outside CSV를 읽는다.
  - required columns: `symbol`, `target_weight`
  - optional columns: `name`, `rationale`
  - duplicate symbol, missing/invalid/negative/out-of-range target weight를 차단한다.
  - `coverage_status`를 `partial_holdings_only` 또는 `full_enough_for_drift`로 구분한다.
  - `--execute`일 때만 `ops.pipeline_run`과 `ref.benchmark_composition` upsert를 수행한다.
- 새 CLI: `stockanalysis-operations benchmark-composition-import-run`
  - `--source-type operator_upload|provider_file`
  - `--min-full-coverage-weight` 기본값 `0.9500`
- 추가 테스트:
  - `tests/test_benchmark_composition_import.py`
  - `tests/test_data_operations_cli.py`
- guardrail 보강:
  - 같은 benchmark/date에 여러 source가 있으면 `provider_file`, `operator_upload`, `manual_seed` 순서로 선택한다.

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_benchmark_composition_import tests.test_data_operations_cli`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_benchmark_composition_import tests.test_portfolio_risk_budget_guardrail tests.test_data_operations_cli`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- Passed: full unittest `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests` with `934 tests OK`.
- Passed: `bash scripts/verify_project_execution_roadmap.sh`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-risk-budget-benchmark-provider-import-v1`
- Passed: `git diff --check`
- Passed on EC2: pulled `8246cae`.
- Passed on EC2: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_benchmark_composition_import tests.test_data_operations_cli`
- Passed on EC2: dry-run CSV import from `/opt/stockanalysis/runtime/spy-operator-holdings-2026-05-25.csv`.
- Passed on EC2: execute CSV import produced `run_id=989`, `coverage_status=partial_holdings_only`, `full_benchmark_drift_interpretation_allowed=false`.
- Passed on EC2: `operator_upload_count=4` for `operator_spy_holdings_2026_05_25`.
- Passed on EC2: risk guardrail rerun produced `run_id=991`, `eval_run_id=22`, `benchmark_source=operator_spy_holdings_2026_05_25`, `source_type=operator_upload`, `composition_coverage_weight=0.215`, `active_share=0.3925`.

## Known Limits

- EC2 smoke CSV is still a partial holdings file, so drift remains partial. It proves the import path and source precedence, not full SPY holdings coverage.
- A full free provider file or broader operator upload is still needed before active share can be interpreted as full benchmark drift.

## Guardrails

- 추천 weight 변경 금지.
- benchmark/evaluation split 변경 금지.
- broker submit, live order, kill switch unlock 금지.
- repo 안 secret/env 값 수정 금지.

## Exact Next Step

- exact next step: `portfolio-risk-budget-drift-quality-audit`를 진행한다. benchmark composition coverage, stale holdings, partial composition warnings, and drift outliers를 data-health/quality audit에 노출한다.
