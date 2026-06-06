# professional-source-gap-actionable-remediation-v1 Contract

## Task Request

- request: Remediate the current actionable `professional_source_gap_attention` without hiding real source limitations or attaching SPY-only source data to QQQ.
- context: `cycle-quality-audit-hardening-v1` 이후 남은 open gate는 `professional_source_gap_attention`이다. 최신 EC2 data-health 기준 결손은 `EROK` source blocker, `QQQ` fund source gaps, `AAPL` equity research artifact gap, `SPY` fund not-applicable managed row로 나뉜다.

## Goal

- goal: Add a free official Invesco QQQ source path for QQQ fund source gaps and make `/api/data-health` remediation commands provider-safe.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/benchmark_composition_provider.py`
  - `src/stockanalysis/operations/fund_expense_ratio_provider.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_benchmark_composition_provider.py`
  - `tests/test_fund_expense_ratio_provider.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/professional-source-gap-actionable-remediation-v1/*`

## Scope

- Add Invesco QQQ official JSON provider imports for holdings, expense ratio, NAV, tracking difference.
- Add CLI commands for QQQ provider imports.
- Update professional source gap remediation text/command provider routing.
- Add tests for parser, runner, CLI wiring, and unsafe SSGA-for-QQQ command prevention.
- Document EC2 follow-up because current SSH is blocked by network/security-group timeout.

## Non-Goals

- Do not change recommendation scoring weights.
- Do not change benchmark definitions beyond source-backed QQQ holdings import capability.
- Do not create broker/order/write flows.
- Do not synthesize missing company financials for EROK.

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_benchmark_composition_provider tests.test_fund_expense_ratio_provider tests.test_data_operations_cli tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task professional-source-gap-actionable-remediation-v1`
