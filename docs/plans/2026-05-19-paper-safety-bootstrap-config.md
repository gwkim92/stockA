# Paper Safety Bootstrap Config Plan

**Goal:** trading readiness의 브로커 경계, 계좌 권한, 주문 한도 누락을 실제 브로커 없이 simulated paper 전용 DB 설정으로 재현 가능하게 채운다.

**Boundary:** 이 작업은 broker secret, broker API, order submit, fill, execution report를 만들지 않는다. `supports_order_submit=false`를 고정하고, global kill switch는 해제하지 않는다.

## Steps

- Add `stockanalysis.trading.paper_safety_bootstrap` SQL renderer/runner.
- Add `stockanalysis-operations paper-safety-bootstrap-config` CLI.
- Upsert paper-only `trading.broker_boundary`, `trading.account_permission`, `trading.order_limit_policy`.
- Keep reports secret-free and mark `submitted_to_broker_count=0`.
- Cover SQL and CLI with unit tests.

## Verification

- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_trading_paper_safety_bootstrap tests.test_data_operations_cli tests.test_trading_paper_validation tests.test_trading_safety`
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest discover -s tests`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task paper-safety-bootstrap-config`
- `git diff --check`
