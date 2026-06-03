# recommendation-evidence-quality-audit-v1 Contract

## Task Request

- request: 추천 목록에서 각 추천의 근거 품질을 바로 판단할 수 있게 한다. 상세 화면을 열기 전에도 뉴스·AI, 상위 흐름, 재무, 피어, 밸류에이션, 산업, AI 리서치, thesis, 페이퍼 검증, 원천 차단 상태를 읽기 전용으로 보여준다.

## Context

- The project already exposes recommendation detail `professional_evidence_audit`, but the recommendation list still hides which rows are ready, source-blocked, or missing evidence.
- The current priority is to make evidence gaps visible before any score or weight change.
- Outcome maturity and manual weight review remain blocked until the existing maturity gates allow them.

## Goal

- goal: `/api/recommendations`와 `/recommendations`가 추천별 `evidence_quality` 요약을 제공하고, ready/gap/source-blocked/paper-pending 상태, coverage, missing layer labels, paper validation status, read-only order boundary를 추천 weight 변경 없이 설명한다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/recommendations/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/recommendation-evidence-quality-audit-v1/*`

## Invariants

- Do not change recommendation score formulas or score weights.
- Do not change benchmark definitions, evaluation split, portfolio positions, broker/order flow, or live trading.
- Do not synthesize missing financial facts for source-blocked symbols.
- Do not start `manual-weight-review-pilot-v1`.

## Scope

- Inspect existing recommendation API/detail payloads.
- Reuse existing backend read adapters and stored evidence.
- Add derived quality summaries where missing.
- Improve UI wording so the user sees what is ready, missing, blocked, and why.
- Add or update tests for payload shape and status derivation.
- Run local verification and EC2 smoke if code changes are deployed.

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-evidence-quality-audit-v1`
- verification command: `git diff --check`

## Definition Of Done

- Recommendation evidence quality is visible in `/api/recommendations` and `/recommendations`.
- Missing/blocked evidence is clearly separated from ready evidence.
- Paper validation and order boundary remain explicit.
- Handoff records implementation, verification, and remaining risks.
