# stocks-page-professional-analysis-clarity-v1 Contract

## Task Request

- request: 종목 상세 화면에서 전문가식 분석 근거가 어디까지 준비됐고 무엇이 빠졌는지 추천 목록과 같은 언어로 바로 보이게 한다.

## Context

- `/recommendations` now exposes recommendation-level `evidence_quality`.
- `/stocks/{symbol}` already has business research, financial model, valuation, industry position, news/cycle impacts, thesis/recommendation links, and source guardrail data.
- The stock page still requires the user to scroll through many sections before understanding which evidence layers are complete, pending, blocked, or not applicable.

## Goal

- goal: `/stocks/{symbol}` 상단에서 사업/AI 리서치, 재무, 피어·산업, 밸류에이션, 뉴스·사이클, 투자 논리, 추천, 가상 매매·실거래 경계를 한 번에 감사하고, 빠진 근거와 다음 클릭 위치를 명확히 보여준다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `docs/tasks/stocks-page-professional-analysis-clarity-v1/*`

## Invariants

- Do not change recommendation score formulas or weights.
- Do not change DB schema, backend API shape, scheduler, AI batch, benchmark definitions, portfolio positions, broker/order flow, or live trading.
- Do not synthesize missing financial facts.
- Use existing read-only stock detail and AI evidence neighborhood data only.

## Scope

- Add a stock-level professional evidence audit panel near the top of `/stocks/{symbol}`.
- Reuse existing data from `StockDetailData` and `AiEvidenceNeighborhoodData`.
- Clearly separate complete, partial, pending, blocked, missing, and not-applicable layers.
- Make ETF/fund boundaries explicit when company financial model is not applicable.
- Keep Korean user-facing copy concise and investment-decision oriented.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task stocks-page-professional-analysis-clarity-v1`
- verification command: `git diff --check`
- verification command: EC2 route smoke for `/stocks/ARM`, `/stocks/SPY`, and `/stocks/EROK`.

## Definition Of Done

- `/stocks/{symbol}` renders a professional evidence audit summary.
- Missing/blocked layers are visible without scrolling to every section.
- ETF/fund and source-blocked cases are explained in Korean.
- Existing read-only order and weight boundaries remain visible.
