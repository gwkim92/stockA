# Task Contract

## Task

- 이름: portfolio-allocation-policy-review-gate
- 요청: 추천 엔진의 소형 `recommended_weight`가 실제 포트폴리오 리밸런싱 목표처럼 해석되어 과도한 `trim_to_target` 티켓을 만드는 문제를 해소한다.
- 담당: Codex
- 날짜: 2026-05-21

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 추천 후보의 4% 같은 진입/신호 비중은 기존 대형 보유를 자동 축소하라는 뜻으로 쓰이지 않는다.
  - 포트폴리오 축소 티켓은 thesis `reduce/exit` 또는 단일 종목 비중 상한 초과 같은 별도 포트폴리오 정책 기준으로만 생성된다.
  - `/remediation`에는 실제로 사람 검토가 필요한 비중 초과 항목만 남는다.

## Scope

- 포함:
  - `portfolio_review` action 정책에 단일 종목 비중 상한 gate 추가
  - 추천 비중과 포트폴리오 리밸런싱 기준을 분리하는 단위 테스트 추가
  - 화면에 노출되는 allocation action/runner label 보강
  - EC2에서 decision-daily systemd service 1회 실행 후 열린 remediation ticket 상태 확인
- 제외:
  - DB schema 변경
  - 추천 점수 산식 변경
  - 브로커 주문, 실거래, paper order 실행
  - 포트폴리오 최적화 엔진 도입

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/signal/portfolio_review.py`
  - `tests/test_portfolio_review_bootstrap.py`
  - `apps/web/src/lib/korean-labels.ts`
  - `docs/tasks/portfolio-allocation-policy-review-gate/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations/schema
  - broker/live order submission
  - recommendation scoring SQL

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_portfolio_review_bootstrap`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_portfolio_review_bootstrap tests.test_portfolio_remediation_ticket`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `cd apps/web && npm run typecheck`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-allocation-policy-review-gate`

## Done Criteria

- [ ] 현재 비중 16%, 추천 비중 4% 같은 “소형 신호 비중 초과”는 `hold`로 남는다.
- [ ] 단일 종목 비중 상한 25% 초과는 `trim_to_target`으로 남는다.
- [ ] 기존 `increase_to_target`, thesis `watch/reduce/exit`, coverage review 동작은 유지된다.
- [ ] UI label이 사람이 읽을 수 있는 한국어로 표시된다.
- [ ] EC2 decision-daily 경로에서 stale/과잉 ticket 상태가 정리된다.
