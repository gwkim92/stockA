# Trading Readiness Blocker Explanations Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 거래 안전 화면에서 paper validation 실패 사유를 원문 코드가 아니라 사람이 이해할 수 있는 한국어 원인과 다음 조치로 보여준다.

**Architecture:** Backend DTO의 `paper_validation.blocked_reasons` contract는 유지한다. Next.js 화면에서 reason code를 안전하게 해석해 표시하고, broker/order write endpoint나 kill switch 변경은 만들지 않는다.

**Tech Stack:** Next.js App Router, TypeScript, existing frontend API DTO, Python unittest/contract verification.

---

## Task 1: Contract

**Files:**
- Create: `docs/tasks/trading-readiness-blocker-explanations/contract.md`
- Create: `docs/tasks/trading-readiness-blocker-explanations/handoff.md`

**Steps:**
- Define no broker submission, no secret exposure, no kill switch unlock.
- Define frontend-only explanation scope.

## Task 2: Reason Translation

**Files:**
- Modify: `apps/web/src/lib/korean-labels.ts`

**Steps:**
- Add blocked reason code labels and `koBlockedReason`.
- Parse `SYMBOL:reason_code` and `position_recommendation_conflict:SYMBOL`.
- Return title, description, next step, and symbol.

## Task 3: Trading Readiness UI

**Files:**
- Modify: `apps/web/src/app/trading-readiness/page.tsx`
- Modify: `apps/web/src/app/globals.css`

**Steps:**
- Render blocked reasons below paper validation summary.
- Keep guardrails visible.
- Display broker 제출 0건 unchanged.

## Task 4: Verification

**Commands:**
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter tests.test_frontend_api_adapter tests.test_trading_paper_validation tests.test_trading_safety`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task trading-readiness-blocker-explanations`
- `git diff --check`
