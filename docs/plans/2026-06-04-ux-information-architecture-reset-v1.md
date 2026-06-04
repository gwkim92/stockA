# UX Information Architecture Reset v1 Implementation Plan

**Goal:** 투자자가 각 화면에서 결론, 이유, 다음 행동을 먼저 보고 세부 원장은 필요할 때만 내려가게 만든다.

**Architecture:** 기존 FastAPI/Next read-only 구조는 유지한다. 첫 단계는 새 API나 schema 없이 Next.js 화면 구조와 공통 CSS를 재정리해 원장 덤프형 화면을 decision-first 화면으로 바꾼다. 데이터 수집, 추천 scoring, broker/order boundary는 변경하지 않는다.

**Tech Stack:** Next.js App Router, React Server Components, TypeScript, existing CSS tokens in `apps/web/src/app/globals.css`.

---

### Task 1: UX Contract And Shared Pattern

**Files:**
- Create: `docs/tasks/ux-information-architecture-reset-v1/contract.md`
- Create: `docs/tasks/ux-information-architecture-reset-v1/handoff.md`
- Modify: `apps/web/src/app/globals.css`

**Step 1: Define decision-first UI rules**

Rules:
- Every page top must answer: `현재 결론`, `왜 중요한가`, `다음 행동`.
- Replace giant generic hero plus repeated 4-card “판정판” with compact decision headers on dense pages.
- Keep logs and raw ledgers below fold.
- Avoid repeating “이 화면은 주문 화면이 아니다” on every page; use one boundary badge or short line.

**Step 2: Add shared CSS**

Add reusable classes:
- `.decision-page`
- `.decision-brief`
- `.decision-brief-kicker`
- `.decision-brief-title`
- `.decision-brief-grid`
- `.decision-card`
- `.decision-flow-nav`
- `.ledger-section`
- `.ledger-section-head`

**Step 3: Verify CSS compiles**

Run:
```bash
cd apps/web && npm run typecheck
```

Expected: PASS.

### Task 2: Events Page IA Reset

**Files:**
- Modify: `apps/web/src/app/events/page.tsx`

**Step 1: Collapse first-screen copy**

Replace the giant hero/command panel with:
- Current data state
- What changed today
- Suspicious or blocked count
- Primary next action

**Step 2: Keep the full event ledger below**

Do not remove data. Move dense list under `ledger-section`.

**Step 3: Verify**

Run:
```bash
cd apps/web && npm run typecheck
```

Expected: PASS.

### Task 3: AI Evidence Index IA Reset

**Files:**
- Modify: `apps/web/src/app/ai-evidence/page.tsx`

**Step 1: Make the page an entry point, not a ledger**

Top shows:
- Accepted/direct evidence count
- Macro-flow evidence count
- Blocked/suppressed count
- Link to latest evidence

**Step 2: Reduce repeated instructions**

Remove duplicate explanatory paragraphs where cards already state the destination.

**Step 3: Verify**

Run:
```bash
cd apps/web && npm run typecheck
```

Expected: PASS.

### Task 4: Blocked And Results Pages IA Reset

**Files:**
- Modify: `apps/web/src/app/ai-evidence/blocked/page.tsx`
- Modify: `apps/web/src/app/ai-evidence/results/page.tsx`

**Step 1: Use clear triage language**

Blocked page top must say:
- `잡음 유지 차단`
- `보강 후보`
- `재처리 전 조건`

Results page top must say:
- `추천 입력 가능`
- `상위 흐름`
- `직접 종목`
- `아직 주문 아님`

**Step 2: Keep raw rows below fold**

Large lists remain reachable but stop dominating the first viewport.

**Step 3: Verify**

Run:
```bash
cd apps/web && npm run typecheck
cd apps/web && npm run build
```

Expected: PASS.

### Task 5: Browser Smoke And Handoff

**Files:**
- Modify: `docs/tasks/ux-information-architecture-reset-v1/handoff.md`

**Step 1: Browser smoke**

Visit:
- local changed build: `http://127.0.0.1:3002/events`
- local changed build: `http://127.0.0.1:3002/ai-evidence`
- local changed build: `http://127.0.0.1:3002/ai-evidence/blocked`
- local changed build: `http://127.0.0.1:3002/ai-evidence/results`

Note: `http://127.0.0.1:13000` is the EC2 Next.js tunnel and only reflects deployed code after deployment.

Confirm first viewport has a compact decision summary, not a giant generic hero.

**Step 2: AWH verify**

Run:
```bash
PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task ux-information-architecture-reset-v1
git diff --check
```

Expected: PASS.

## Current Implementation Status

- implemented: shared decision-first CSS.
- implemented: `/events` decision summary and ledger split.
- implemented: `/ai-evidence` direct/macro/blocked entry point.
- implemented: `/ai-evidence/blocked` total blocked count and latest displayed ledger clarification.
- implemented: `/ai-evidence/results` direct/macro/cluster/no-order split.
- verified: typecheck, build, AWH, `git diff --check`, desktop and mobile route smoke.
