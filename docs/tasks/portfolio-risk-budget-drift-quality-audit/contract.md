# Task Contract

## Task

- 이름: portfolio-risk-budget-drift-quality-audit
- 요청: benchmark drift를 계산했다는 사실만 보여주는 것이 아니라, benchmark composition 품질을 data-health/quality 화면에서 판단 가능하게 만든다.
- 담당: Codex
- 날짜: 2026-05-26

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/api/data-health`와 `/data-health`가 최신 `portfolio_risk_budget_guardrail`의 benchmark drift 품질을 읽고, composition coverage, stale source, partial composition warning, active share/outlier 상태를 사용자 언어로 보여준다.

## Scope

- 포함:
  - 최신 `portfolio_risk_budget_guardrail` eval의 `benchmark_drift`를 data-health payload로 연결
  - benchmark composition coverage, source type/name/as-of-date, active share, top active positions 요약
  - stale composition, partial composition, missing composition, drift outlier 품질 판정
  - `/data-health`에 사용자용 benchmark drift 품질 카드 추가
  - unit/type/build 검증
- 제외:
  - recommendation scoring weight 변경
  - benchmark/evaluation split 변경
  - full SPY holdings provider 자동 다운로드
  - broker submit/live order flow
  - kill switch unlock

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/lib/types.ts`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/portfolio-risk-budget-drift-quality-audit/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
- 수정 금지 파일:
  - 추천 scoring formula/weights
  - benchmark/evaluation split
  - broker/order submit path
  - repo 안 secret/env 값

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter tests.test_portfolio_risk_budget_guardrail`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `cd apps/web && npm run typecheck && npm run build`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-risk-budget-drift-quality-audit`
  - `git diff --check`

## Done Criteria

- `/api/data-health` returns `benchmark_drift_quality`.
- `/data-health` shows whether benchmark drift is full-enough, partial, stale, missing, or outlier-heavy.
- Partial composition is not presented as full benchmark active share.
- Recommendation weights, paper validation rule, broker submit, and live order behavior remain unchanged.
