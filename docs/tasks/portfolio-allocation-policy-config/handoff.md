# Session Handoff

## Current Status

- 상태: implemented, pushed, and EC2 smoke passed.
- 기준일: 2026-05-22
- 완료:
  - 작업 범위와 mutable surface를 `contract.md`에 고정했다.
  - `portfolio.allocation_policy` migration을 추가했다.
  - active global default policy를 migration에 포함했다.
  - portfolio review candidate lookup이 정책 값을 읽고, 없으면 기본값으로 fallback한다.
  - `PortfolioReviewCandidate`에 `allocation_policy_id`, `max_single_position_weight`, `min_rebalance_target_weight`를 추가했다.
  - 단위 테스트로 정책별 `trim_to_target`/`hold` 동작을 검증했다.
  - 단일 종목 상한이 `watch` thesis action에 의해 숨지 않도록 action 우선순위를 조정했다.
  - EC2에 migration을 적용했고 default policy row `0.2500/0.1000`을 확인했다.
  - EC2 `decision-daily` smoke가 `completed`, 실패 0건으로 완료됐다.
  - 최신 `/remediation`은 MSFT/TSLA 2건을 단일 종목 25% 상한 초과 비중 검토로 표시한다.
- 막힌 점:
  - 없음.

## Implemented

- Added `db/migrations/0015_portfolio_allocation_policy.sql`.
- Updated `src/stockanalysis/signal/portfolio_review.py`.
- Updated `tests/test_portfolio_review_bootstrap.py`.
- Added `tests/test_portfolio_allocation_policy.py`.

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_portfolio_review_bootstrap tests.test_portfolio_allocation_policy`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_portfolio_review_bootstrap tests.test_portfolio_remediation_ticket tests.test_portfolio_allocation_policy`
- Passed after action priority adjustment: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_portfolio_review_bootstrap tests.test_portfolio_remediation_ticket tests.test_portfolio_allocation_policy`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- Passed: `bash scripts/verify_migrations.sh`
- Passed: `git diff --check`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-allocation-policy-config`
- Passed on EC2: migration `0015_portfolio_allocation_policy.sql` applied to `stockanalysis-postgres`.
- Passed on EC2: policy count 1 with `max_single_position_weight=0.2500`, `min_rebalance_target_weight=0.1000`.
- Passed on EC2: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_portfolio_review_bootstrap tests.test_portfolio_remediation_ticket tests.test_portfolio_allocation_policy`
- Passed on EC2: `stockanalysis-operating-data-decision-daily.service` returned `Result=success`, `ExecMainStatus=0`.
- Passed on EC2: latest decision-daily report generated at `2026-05-22T01:12:54Z` with `run_status=completed`, `failed_step_count=0`, remediation `ticket_count=2`.
- Passed via local tunnel: `/remediation` renders MSFT/TSLA allocation review tickets and `/__health` returns `status=ok`.

## Remaining

- Decide whether the default 25% cap should remain global or be overridden with a portfolio-specific row for `Long Term Paper`.
- Add read-only API/UI visibility for the active allocation policy if the operator needs to see the exact policy source on screen.

## Exact Next Step

- exact next step: expose active allocation policy on `/remediation` or portfolio coverage so the operator can see why MSFT/TSLA are flagged.
