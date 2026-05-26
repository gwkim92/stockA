# Session Handoff

## Current Status

- 완료: benchmark composition storage, manual MVP seed, risk guardrail drift 계산, readiness DTO passthrough, 최소 화면 문구 반영, EC2 smoke까지 확인했다.

## Implementation Notes

- 새 migration: `db/migrations/0023_benchmark_composition.sql`
  - `ref.benchmark_composition`에 benchmark code, 구성 종목, target weight, source metadata, valid window를 저장한다.
- 새 seed: `db/seeds/0006_benchmark_composition_seed.sql`
  - `SPY`에 대해 `manual_seed` / `mvp_manual_spy_component_seed` 부분 구성비를 넣는다.
  - 이 값은 drift 계산 경로를 검증하기 위한 수동 seed이며 최신 ETF holdings라고 주장하지 않는다.
- `portfolio-risk-budget-guardrail-run`
  - composition이 있으면 `benchmark_drift.status=calculated_partial_composition`, `active_share`, `top_active_positions`를 계산한다.
  - composition이 없으면 기존처럼 `insufficient_benchmark_composition`을 유지한다.
- `/api/trading/readiness`
  - latest guardrail eval의 `benchmark_drift`를 반환한다.
- `/paper-trading`, `/portfolio/coverage`
  - benchmark drift가 계산되면 active share/percent를 표시한다.

## Guardrails

- 추천 weight 변경 금지.
- benchmark/evaluation split 변경 금지.
- broker submit, live order, kill switch unlock 금지.
- external paid data provider 금지.

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_portfolio_risk_budget_guardrail tests.test_data_operations_cli`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter tests.test_trading_paper_validation`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- Passed: `cd apps/web && npm run typecheck`
- Passed: `cd apps/web && npm run build`
- Passed: `DDL_VERIFY_INCLUDE_SEEDS=1 bash scripts/verify_migrations.sh`
- Passed: `git diff --check`
- Passed: `bash scripts/verify_project_execution_roadmap.sh`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-risk-budget-benchmark-composition-v1`
- Passed: full unittest `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests` with `926 tests OK`.
- Passed on EC2: migration and seed applied, `ref.benchmark_composition` SPY count `4`.
- Passed on EC2: focused tests `tests.test_portfolio_risk_budget_guardrail` and `tests.test_frontend_live_adapter tests.test_portfolio_risk_budget_guardrail`.
- Passed on EC2: `portfolio-risk-budget-guardrail-run --execute` produced `run_id=977`, `eval_run_id=20`, `benchmark_drift.status=calculated_partial_composition`, `active_share=0.3925`.
- Passed on EC2: `cd apps/web && npm run build`.
- Passed on EC2: `stockanalysis-frontend-api.service` and `stockanalysis-web.service` active.
- Passed on EC2: `/api/trading/readiness` exposes `active_share`.
- Passed on EC2: `/paper-trading` exposes active share wording.
- Passed on EC2: `/portfolio/coverage` exposes measured benchmark drift percent `39.3%`.

## Known Limits

- The current `SPY` composition is a partial manual MVP seed, not a complete provider holdings file.
- Drift is calculated but marked `calculated_partial_composition`; it should not be interpreted as full index active share until a validated dated holdings source reaches high coverage.

## Exact Next Step

- exact next step: `portfolio-risk-budget-benchmark-provider-import-v1`을 진행한다. 무료 provider file 또는 operator upload 방식으로 dated benchmark holdings를 검증 후 `ref.benchmark_composition`에 넣고, coverage가 충분할 때만 full benchmark drift로 승격한다.
