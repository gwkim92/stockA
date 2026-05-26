# Task Contract

## Task

- 이름: portfolio-risk-budget-rebalance-candidate-review
- 요청: full benchmark drift에서 드러난 active weight outlier를 자동 주문이 아니라 검토 가능한 리밸런싱 후보로 정리한다.
- 담당: Codex
- 날짜: 2026-05-26

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 최신 `portfolio_risk_budget_guardrail`의 `benchmark_drift.top_active_positions`를 읽어 active overweight/underweight 후보를 backend DTO에 명시하고, 화면에서 `TSLA/MSFT/AAPL` 같은 과대 active weight 종목을 왜 검토해야 하는지 주문 없이 확인할 수 있다.

## Scope

- 포함:
  - `benchmark_drift` 기반 deterministic rebalance candidate payload 생성
  - 후보별 `symbol`, `current_weight`, `benchmark_weight`, `active_weight`, `direction`, `severity`, `suggested_review_action`, `rationale`, `order_boundary` 노출
  - `/api/trading/readiness`의 `portfolio_risk_budget_guardrail` DTO 확장
  - `/api/portfolio/{portfolio}/coverage` risk budget DTO에서 동일 후보를 사용 가능하게 노출
  - `/portfolio/coverage`, `/paper-trading`, `/trading-readiness`에 사람이 이해 가능한 검토 카드/표시 추가
  - unit/adapter/frontend type/build 검증
- 제외:
  - 추천 scoring weight 변경
  - 자동 리밸런싱 계산 또는 목표 주문 수량 산출
  - broker submit, live order, kill switch unlock
  - benchmark/evaluation split 변경
  - 새 유료 데이터 provider 도입

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/portfolio/coverage/page.tsx`
  - `apps/web/src/app/paper-trading/page.tsx`
  - `apps/web/src/app/trading-readiness/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/portfolio-risk-budget-rebalance-candidate-review/*`
  - `docs/plans/2026-05-26-portfolio-risk-budget-rebalance-candidate-review.md`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
- 수정 금지 파일:
  - 추천 scoring formula/weights
  - broker/order submit path
  - repo 안 secret/env 값
  - benchmark/evaluation split

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `cd apps/web && npm run typecheck && npm run build`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-risk-budget-rebalance-candidate-review`
  - `git diff --check`

## Done Criteria

- API DTO가 latest guardrail benchmark drift에서 review candidates를 만든다.
- 후보는 read-only이며 `order_boundary=read_only_no_order`를 가진다.
- 화면은 active overweight/underweight를 “주문”이 아니라 “검토 후보”로 설명한다.
- 추천 weights, broker submit, automatic order flags는 변경되지 않는다.
- EC2 route/API smoke에서 candidates가 확인된다.
