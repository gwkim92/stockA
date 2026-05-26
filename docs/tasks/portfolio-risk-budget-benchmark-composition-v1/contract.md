# Task Contract

## Task

- 이름: portfolio-risk-budget-benchmark-composition-v1
- 요청: 포트폴리오 위험 예산 guardrail이 benchmark drift를 임의 추정하지 않고 canonical Postgres의 명시적 benchmark composition을 읽어 계산하도록 만든다.
- 담당: Codex
- 날짜: 2026-05-26

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `stockanalysis-operations portfolio-risk-budget-guardrail-run --portfolio-name ... --as-of-date YYYY-MM-DD --execute`가 `ref.benchmark_composition`에 저장된 명시적 benchmark 구성비를 읽어 active weight drift를 계산하고, 구성비가 없으면 기존처럼 `insufficient_benchmark_composition`으로 남기며, 추천 weight와 주문 경로는 바꾸지 않는다.

## Scope

- 포함:
  - `ref.benchmark_composition` migration 추가
  - clearly labeled manual MVP benchmark composition seed 추가
  - risk budget guardrail state lookup/report builder의 drift 계산 확장
  - `/api/trading/readiness` guardrail payload의 benchmark drift passthrough
  - paper/portfolio 화면의 계산됨/미계산 문구 최소 반영
  - available/unavailable benchmark composition 테스트
  - roadmap/handoff 정리
- 제외:
  - paid benchmark/ETF data provider
  - automatic provider scraper
  - recommendation score weight changes
  - live broker/order submit
  - full frontend drift charting

## Mutable Surface

- 수정 가능한 파일:
  - `db/migrations/0023_benchmark_composition.sql`
  - `db/seeds/0006_benchmark_composition_seed.sql`
  - `db/seeds/README.md`
  - `src/stockanalysis/operations/portfolio_risk_budget_guardrail.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/korean-labels.ts`
  - `apps/web/src/app/paper-trading/page.tsx`
  - `apps/web/src/app/portfolio/coverage/page.tsx`
  - `tests/test_portfolio_risk_budget_guardrail.py`
  - `scripts/verify_migrations.sh`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/portfolio-risk-budget-benchmark-composition-v1/*`
- 수정 금지 파일:
  - 추천 scoring formula/weights
  - benchmark/evaluation split
  - broker/order submit path
  - kill switch unlock
  - repo 안 secret/env 값

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_portfolio_risk_budget_guardrail tests.test_data_operations_cli`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter tests.test_trading_paper_validation`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `DDL_VERIFY_INCLUDE_SEEDS=1 bash scripts/verify_migrations.sh`
  - `git diff --check`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-risk-budget-benchmark-composition-v1`

## Rollback

- Remove `db/migrations/0023_benchmark_composition.sql`.
- Remove `db/seeds/0006_benchmark_composition_seed.sql`.
- Revert `portfolio_risk_budget_guardrail` benchmark drift calculation changes.
- Existing fallback path remains `insufficient_benchmark_composition`.

## Done Criteria

- migration and seed apply on disposable Postgres.
- guardrail report calculates benchmark drift when composition exists.
- guardrail report keeps explicit unavailable state when composition is missing.
- frontend API includes benchmark drift metadata without requiring browser secrets.
- recommendation weights, broker submit, live order flow, and kill switch state are unchanged.
