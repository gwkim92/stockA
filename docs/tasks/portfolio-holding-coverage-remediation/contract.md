# Task Contract

## Task

- 이름: portfolio-holding-coverage-remediation
- 요청: 보유 중인 종목이 최신 recommendation row에 없더라도 active holding thesis가 있으면 paper validation에서 recommendation coverage gap으로 오탐하지 않게 한다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/api/paper-trading/preview` live SQL이 position `linked_thesis_id`를 recommendation thesis coverage로 인정하여, active thesis가 있는 보유 종목을 `position_recommendation_conflict`로 계산하지 않는다.

## Scope

- 포함:
  - paper trading preview SQL의 `thesis_id` fallback을 `coalesce(recommendation.thesis_id, position.linked_thesis_id)`로 변경
  - recommendation row가 없고 current holding이 있어도 linked thesis가 있으면 `paper_hold`로 처리
  - recommendation row도 linked thesis도 없는 보유 종목만 `paper_review_no_recommendation` conflict로 유지
  - unit test로 SQL condition 고정
  - EC2 live paper validation dry-run/smoke
- 제외:
  - 추천 score/weight 변경
  - active thesis 자동 생성 로직 변경
  - paper validation historical row 수정
  - kill switch/human approval 해제
  - broker submit

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/portfolio-holding-coverage-remediation/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
- 수정 금지 파일:
  - `src/stockanalysis/signal/recommendation.py`
  - `src/stockanalysis/signal/portfolio_holding_thesis.py`
  - DB migrations/schema
  - broker/order submit path
  - `.env` secret values

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter tests.test_paper_validation_conflict_remediation`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-holding-coverage-remediation`

## Done Criteria

- active linked thesis가 있는 AAPL/MSFT/TSLA 같은 보유 종목은 최신 recommendation row가 없어도 paper conflict로 오탐되지 않는다.
- recommendation row도 linked thesis도 없는 보유 종목은 여전히 conflict로 남는다.
- paper preview와 paper validation은 여전히 실제 주문을 만들지 않는다.
- kill switch/human approval safety interlock은 그대로 유지된다.
