# Task Contract

## Task

- 이름: portfolio-risk-budget-frontend-guardrail-visibility
- 요청: persisted portfolio risk budget guardrail과 paper validation 차단 사유를 portfolio/paper/trading safety 화면에서 이해 가능하게 보여준다.
- 담당: Codex
- 날짜: 2026-05-26

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/api/trading/readiness`가 최신 `portfolio_risk_budget_guardrail` eval 상태를 반환하고, `/paper-trading`, `/trading-readiness`, `/portfolio/coverage`가 이 상태를 한국어로 표시해 “가상 검증이 왜 막혔는지”를 사용자가 이해할 수 있다.

## Scope

- 포함:
  - trading readiness live DTO에 risk budget guardrail payload 추가
  - trading readiness gate에 `portfolio_risk_budget_guardrail` 추가
  - paper trading 화면에 risk budget 연결 상태 카드 추가
  - trading readiness 화면에 risk budget blocker 섹션 추가
  - portfolio coverage 화면에 persisted guardrail 요약 추가
  - 한국어 reason mapping 추가
  - tests/typecheck/build/EC2 route smoke
- 제외:
  - 신규 DB migration
  - risk budget 산식 변경
  - paper validation writer 변경
  - 추천 score/weight 변경
  - broker submit, kill switch unlock

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/korean-labels.ts`
  - `apps/web/src/app/paper-trading/page.tsx`
  - `apps/web/src/app/trading-readiness/page.tsx`
  - `apps/web/src/app/portfolio/coverage/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/portfolio-risk-budget-frontend-guardrail-visibility/*`
- 수정 금지 파일:
  - 추천 scoring formula/weights
  - trading write path
  - broker/order submit path
  - repo 안 secret/env 값

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-risk-budget-frontend-guardrail-visibility`

## Done Criteria

- `/api/trading/readiness`는 guardrail eval id, decision, paper validation input permission, blockers, warnings를 반환한다.
- paper/trading/portfolio 화면은 risk budget blocker를 한국어로 보여준다.
- 사용자는 `conflict_count=0`이어도 왜 paper validation이 실패인지 이해할 수 있다.
- broker submit과 추천 weight는 계속 변경되지 않는다.
