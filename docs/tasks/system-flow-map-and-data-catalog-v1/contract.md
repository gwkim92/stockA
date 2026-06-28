# system-flow-map-and-data-catalog-v1 Contract

## Task Request

- request: 프로젝트를 중장기 투자 판단 운영 시스템으로 정리하고, 데이터 수집부터 성과 피드백까지 전체 흐름과 데이터 사용 경계를 고정한다.

## Goal

- goal: `수집 -> 품질 검증 -> AI 구조화 -> 사이클/기업/ETF 분석 -> 추천·보유·페이퍼 검증 -> 성과 피드백` 흐름을 문서와 운영 화면에 명확히 드러낸다.

## Mutable Surface

- mutable surface:
  - `docs/system-flow-map.md`
  - `docs/data-catalog.md`
  - `docs/tasks/system-flow-map-and-data-catalog-v1/*`
  - `apps/web/src/app/data-health/**`
  - `apps/web/src/app/admin/ai-agents/**`
  - `apps/web/src/app/stocks/[symbol]/**`
  - `apps/web/src/components/recommendation-position-reality.tsx`
  - `apps/web/src/components/operations/**`
  - `apps/web/src/lib/presentation/**`
  - `apps/web/tests/e2e/investment-workspace.spec.ts`
  - `docs/api/frontend/examples/*`
  - `src/stockanalysis/frontend/api_adapter.py`
  - `tests/test_frontend_api_adapter.py`

## Invariants

- Do not change recommendation scoring weights.
- Do not change benchmark definitions, portfolio positions, broker/order flow, or live trading behavior.
- Do not introduce paid external RAG, vector DB, graph DB, or new managed services.
- Do not perform large DB schema changes.
- Keep existing route URLs and API DTO compatibility.
- Keep AI as interpretation/structuring/reporting; deterministic code owns score, constraints, paper validation, and order boundary.

## Scope

- Add system flow and data catalog documentation.
- Document operating profile dependency and freshness expectations.
- Improve `/data-health` top-level decision-flow visibility.
- Improve AI prompt/model/eval visibility in operations screens.
- Surface data gaps as source limits or zero-weight evidence rather than hidden failures.
- Increase `/stocks/[symbol]` first viewport density for company stock versus ETF/fund cases.
- Add fixture-only visual QA examples where needed without expanding the public frontend API contract endpoint list.

## Verification

- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task system-flow-map-and-data-catalog-v1`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm test`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`

## Done Criteria

- [x] `docs/system-flow-map.md` exists and fixes the end-to-end architecture.
- [x] `docs/data-catalog.md` exists and classifies data by collection, normalization, AI input, recommendation input, display, zero-weight, and blocked use.
- [x] `/data-health` has a decision-flow status view for news/AI, market prices, cross-asset, Toss broker reality, recommendations/holdings, and performance feedback.
- [x] `/admin/ai-agents` exposes provider, prompt version, output schema, caps, fallback, and evaluation/quality checks without implying realtime AI calls from the UI.
- [x] `/stocks/[symbol]` first viewport shows product type, daily change, price, holding status, average cost, unrealized P/L, analysis price state, and Toss broker reality state.
- [x] Verification commands pass or remaining failures are documented.
