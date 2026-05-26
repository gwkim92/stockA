# financial-statement-model-detail-v1 Contract

## Task Request

- request: 기존 `market.financial_metric_normalized` 데이터를 종목 상세 API와 화면에서 애널리스트식 재무 모델로 볼 수 있게 만든다.

전문 주식 분석 시스템으로 가려면 뉴스·사이클만이 아니라 매출 성장, 마진, 현금흐름, 부채, 투자 부담, 이익 품질, 희석 여부를 한 화면에서 확인할 수 있어야 한다. 이번 작업은 이미 산출된 정규화 재무 지표를 read-only DTO와 한국어 화면으로 연결한다.

## Goal

- goal: `/api/stocks/{symbol}`과 `/stocks/[symbol]`에서 재무제표 모델을 성장, 수익성, 현금흐름, 재무상태, 투자 부담, 이익 품질, 희석·주식수 섹션으로 확인할 수 있게 한다. 추천 score, score weight, benchmark, broker/order boundary는 변경하지 않는다.

## Purpose

Make normalized financial statements visible as an analyst-style model on stock detail pages. The project already computes normalized metrics and zero-weight fundamental components, but users cannot inspect the actual revenue, margin, cash-flow, balance-sheet, dilution, and earnings-quality evidence in one place.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `docs/tasks/financial-statement-model-detail-v1/*`
  - `docs/plans/2026-05-26-financial-statement-model-detail-v1.md`
  - `docs/tasks/valuation-target-range-foundation-v1/handoff.md`
  - `docs/tasks/valuation-target-range-foundation-v1/review.md`

## Must Be True When Complete

- `/api/stocks/{symbol}` live response includes a read-only `financial_statement_model` object built from existing `market.financial_metric_normalized` rows.
- The model separates metrics into analyst-readable sections: growth, profitability, cash-flow quality, balance-sheet risk, capital intensity, and earnings quality.
- The payload exposes latest period, period coverage, computed/unavailable/insufficient-history counts, source run ids, and per-metric rationale/status.
- `/stocks/[symbol]` renders a Korean financial model section that explains what is known, what is missing, and why it matters.
- Recommendation scoring weights, benchmark/evaluation splits, and broker/order boundaries remain unchanged.

## In Scope

- Stock detail live adapter SQL and DTO shaping.
- TypeScript contract updates.
- Stock detail frontend section and professional research step wiring.
- Unit tests for API shape and SQL coverage.
- Task handoff/review documentation.

## Out Of Scope

- New financial metric formulas.
- SEC ingest or financial normalization runner changes.
- Recommendation score formula or component weight changes.
- Live broker submit, automatic orders, or kill-switch unlock.
- New database schema.

## Verification Plan

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task financial-statement-model-detail-v1`

## Completion Checklist

- [ ] Stock detail SQL reads `market.financial_metric_normalized`.
- [ ] DTO returns `financial_statement_model`.
- [ ] UI shows financial model in Korean and avoids developer-only wording.
- [ ] Missing data is shown as a data gap, not hidden.
- [ ] Recommendation weights and order boundary remain unchanged.
- [ ] Handoff contains verification evidence and remaining risks.
