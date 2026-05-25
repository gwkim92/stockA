# Task Contract

## Task

- 이름: portfolio-risk-budget-visibility
- 요청: 기존 portfolio allocation policy를 포트폴리오 커버리지 API와 화면에 연결해 포지션 크기와 위험 예산 상태를 투자자가 이해할 수 있게 보여준다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/api/portfolio/{portfolio}/coverage` live payload가 현재 적용 allocation policy, risk budget summary, position별 size status를 반환하고, `/portfolio/coverage` 화면이 단일 종목 한도, 리밸런싱 기준, 초과 포지션 여부를 한국어로 보여준다.

## Scope

- 포함:
  - 기존 `portfolio.allocation_policy` read model 재사용
  - portfolio coverage DTO에 `allocation_policy`, `risk_budget`, position size fields 추가
  - portfolio coverage 화면에 위험 예산/포지션 크기 섹션 추가
  - live adapter contract test 갱신
- 제외:
  - 신규 schema/migration
  - 추천 점수 산식 또는 weight 변경
  - 실제 리밸런싱 주문/브로커 submit
  - 사용자별 risk preference 입력 UI
  - repo 안 secret/env 값

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/app/portfolio/coverage/page.tsx`
  - `apps/web/src/lib/types.ts`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/portfolio-risk-budget-visibility/*`
- 수정 금지 파일:
  - DB schema/migration
  - recommendation score formula
  - broker/order submit path
  - repo 안 secret/env 값

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-risk-budget-visibility`

## Done Criteria

- allocation policy가 포트폴리오 커버리지 API에 포함된다.
- 각 position은 `within_budget`, `below_rebalance_floor`, `over_single_position_limit` 중 하나의 size status를 가진다.
- risk budget summary는 최대 보유 종목, 초과 포지션 수, 리밸런싱 기준 미만 포지션 수를 반환한다.
- 화면은 이 정보가 실제 주문이 아니라 보유 검토/포지션 사이징 입력임을 명확히 표시한다.
