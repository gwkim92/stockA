# Session Handoff

## Current Status

- 상태: implemented locally, pending commit/deploy.
- 기준일: 2026-05-22
- 완료:
  - 작업 범위와 mutable surface를 `contract.md`에 고정했다.
  - `portfolio.allocation_policy` migration을 추가했다.
  - active global default policy를 migration에 포함했다.
  - portfolio review candidate lookup이 정책 값을 읽고, 없으면 기본값으로 fallback한다.
  - `PortfolioReviewCandidate`에 `allocation_policy_id`, `max_single_position_weight`, `min_rebalance_target_weight`를 추가했다.
  - 단위 테스트로 정책별 `trim_to_target`/`hold` 동작을 검증했다.
  - 단일 종목 상한이 `watch` thesis action에 의해 숨지 않도록 action 우선순위를 조정했다.
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

## Remaining

- Commit and push.
- Deploy to EC2.
- Apply migration on EC2.
- Run decision-daily smoke and confirm data-health/remediation remain healthy.

## Exact Next Step

- exact next step: run AWH verify, then commit/push and deploy.
