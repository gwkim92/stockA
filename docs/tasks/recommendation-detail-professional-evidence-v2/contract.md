# recommendation-detail-professional-evidence-v2 Contract

## Task Request

- request: 추천 상세 화면에서 한 추천이 전문 분석 기준으로 어디까지 검토 가능한지 보여준다. 재무, 피어, 밸류에이션, 산업, AI 리서치, thesis, 페이퍼 검증, 주문 경계를 한 화면에서 추적 가능하게 만든다.

## Goal

- goal: `/api/recommendations/{id}`와 `/recommendations/{id}`가 추천 단위 `professional_evidence_audit`을 제공하고, source blocker, coverage gap, paper validation pending, read-only order boundary를 추천 weight 변경 없이 설명한다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/recommendation-detail-professional-evidence-v2/*`

## Invariants

- Do not change recommendation scoring weights.
- Do not change benchmark definitions, portfolio positions, broker/order flow, live trading, or paper trade execution behavior.
- Do not synthesize missing financial facts for source-blocked symbols.
- Do not introduce paid external RAG, vector, or graph services.

## Scope

- Add a read-only `professional_evidence_audit` recommendation detail payload.
- Derive audit status from existing detail evidence: cycle, news/AI, financial model, peer, valuation, industry, AI research, thesis, paper validation, and source guardrail.
- Render a Korean audit section in `/recommendations/[recommendationId]`.
- Preserve all order and weight boundaries as blocked/read-only.

## Verification

- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task recommendation-detail-professional-evidence-v2`
- verification command: `git diff --check`

## Done Criteria

- [ ] `/api/recommendations/{id}` includes `professional_evidence_audit`.
- [ ] Audit payload shows layer checks, source blocker, paper validation, scoring boundary, and order boundary.
- [ ] `/recommendations/{id}` renders the recommendation-level professional audit in Korean.
- [ ] Local verification passes.
- [ ] EC2 route smoke confirms live rendering.
