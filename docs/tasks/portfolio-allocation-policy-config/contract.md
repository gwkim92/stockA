# Task Contract

## Task

- 이름: portfolio-allocation-policy-config
- 요청: 포트폴리오 검토의 단일 종목 비중 상한과 리밸런싱 목표 해석 기준을 코드 상수가 아니라 포트폴리오/전략별 정책으로 분리한다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `portfolio.allocation_policy`에서 active 정책을 읽어 포트폴리오 검토 action을 계산한다.
  - 정책 row가 없거나 테스트 payload가 구버전이면 안전한 기본값으로 동작한다.
  - 추천 신호 비중과 실제 포트폴리오 리밸런싱 정책의 책임이 분리된다.

## Scope

- 포함:
  - `portfolio.allocation_policy` migration 추가
  - global 기본 정책 row 추가
  - portfolio review candidate lookup에 정책 join 추가
  - `PortfolioReviewCandidate`에 정책 필드 추가
  - 정책별 trim/hold 동작 단위 테스트 추가
  - EC2 migration 적용과 decision-daily smoke
- 제외:
  - 포트폴리오 최적화 엔진
  - 추천 점수 산식 변경
  - broker/order flow
  - 화면에서 정책 편집 write API

## Mutable Surface

- 수정 가능한 파일:
  - `db/migrations/0015_portfolio_allocation_policy.sql`
  - `src/stockanalysis/signal/portfolio_review.py`
  - `tests/test_portfolio_review_bootstrap.py`
  - `tests/test_portfolio_allocation_policy.py`
  - `docs/tasks/portfolio-allocation-policy-config/*`
- 수정 금지 파일:
  - `.env` secret values
  - broker/live order submission
  - recommendation scoring SQL

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_portfolio_review_bootstrap tests.test_portfolio_allocation_policy`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_portfolio_review_bootstrap tests.test_portfolio_remediation_ticket tests.test_portfolio_allocation_policy`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `bash scripts/verify_migrations.sh`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-allocation-policy-config`

## Done Criteria

- [ ] Migration creates `portfolio.allocation_policy`.
- [ ] Default active global policy exists.
- [ ] Candidate lookup includes policy values with fallback defaults.
- [ ] A portfolio-specific cap can prevent or trigger `trim_to_target`.
- [ ] Existing coverage/thesis/recommendation review behavior remains unchanged.
- [ ] EC2 applies migration and latest decision-daily run completes.
