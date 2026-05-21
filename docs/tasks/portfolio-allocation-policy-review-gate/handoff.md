# Session Handoff

## Current Status

- 상태: in_progress
- 기준일: 2026-05-21
- 완료:
  - EC2 `decision-daily` systemd service를 수동으로 1회 실행해 자동 경로가 성공하는지 확인했다.
  - 새 `portfolio-holding-thesis-bootstrap` step은 decision-daily profile 안에서 정상 실행됐다.
  - 새로 열린 remediation ticket은 thesis 누락이 아니라 allocation review였다.
  - 원인 확인: `recommended_weight=0.0400` 같은 추천 신호 비중이 실제 포트폴리오 축소 목표처럼 사용되어 `trim_to_target`이 과도하게 생성됐다.
  - 로컬 코드에서 추천 비중과 포트폴리오 축소 gate를 분리했다.
- 막힌 점:
  - 아직 EC2 배포와 live decision-daily 재실행은 남아 있다.

## Implemented

- `src/stockanalysis/signal/portfolio_review.py`
  - 단일 종목 검토 상한 `_MAX_SINGLE_POSITION_WEIGHT = 0.2500` 추가.
  - 추천 비중이 10% 미만인 경우에는 기존 보유 축소 목표로 쓰지 않도록 분리.
  - 단일 종목 비중 상한 초과 또는 명시적 thesis reduce/exit일 때만 축소 검토가 생성되도록 조정.
- `tests/test_portfolio_review_bootstrap.py`
  - 16% 보유, 4% 추천 신호는 `hold`로 남는 회귀 테스트 추가.
  - 31% 보유, 4% 추천 신호는 단일 종목 상한 초과로 `trim_to_target`이 되는 테스트 추가.
- `apps/web/src/lib/korean-labels.ts`
  - allocation action/runner label 추가.
  - 새/기존 portfolio review reason 문장을 모두 한국어로 파싱하도록 보강.

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_portfolio_review_bootstrap`
- Passed: `cd apps/web && npm run typecheck`

## Remaining

- Run broader focused regression:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_portfolio_review_bootstrap tests.test_portfolio_remediation_ticket`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - AWH verify for `portfolio-allocation-policy-review-gate`
- Commit/push.
- Deploy to EC2, restart API/Web if needed.
- Run EC2 `decision-daily` service once and confirm open tickets are now only true allocation cap breaches.

## Exact Next Step

- exact next step: run the focused regression suite and AWH verify locally before committing.
