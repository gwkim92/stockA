# AI Evidence Story Groups Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a free, deterministic story-group layer to the AI evidence neighborhood so users can see which news items belong to the same investable narrative and why they are connected.

**Architecture:** Keep the canonical database unchanged. Build story groups at the read-only frontend API boundary from existing event, document, chunk, theme, and artifact payloads. Render the groups on stock detail as explanation UI, not as investment recommendation or order signal.

**Tech Stack:** Python stdlib, FastAPI live adapter DTOs, Next.js server components, TypeScript contract types, unittest, existing AWH task harness.

---

### Task 1: Task Harness

**Files:**
- Create: `docs/tasks/ai-evidence-story-groups/contract.md`
- Create: `docs/tasks/ai-evidence-story-groups/handoff.md`
- Create: `docs/tasks/ai-evidence-story-groups/review.md`

**Steps:**
- Define scope as read-only AI/RAG explainability only.
- Exclude live LLM calls, vector DB, recommendation scoring, broker writes, and scheduler activation.
- Record verification commands before implementation.

### Task 2: Backend DTO Story Groups

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Test: `tests/test_frontend_live_adapter.py`

**Steps:**
- Add a local deterministic title token/signature helper.
- Add story group payloads to `/api/ai/evidence-neighborhoods/{symbol}`.
- Each group should include representative title, events, source document ids, linked chunk ids, theme keys, relation reasons, token/cost boundary, and a confidence value that is clearly heuristic.
- Write tests against the fake live executor payload to assert story groups are present, read-only, and do not expose secrets.

### Task 3: TypeScript Contract

**Files:**
- Modify: `apps/web/src/lib/types.ts`

**Steps:**
- Add `story_groups` to `AiEvidenceNeighborhoodData`.
- Keep it optional only if necessary for backwards compatibility; prefer required if API always emits it.

### Task 4: Stock Detail UI

**Files:**
- Modify: `apps/web/src/app/stocks/[symbol]/page.tsx`

**Steps:**
- Add a “뉴스 이야기 묶음” section inside `EvidenceNeighborhoodPanel`.
- Show why the group exists: same headline signature, same source document, same theme, same symbol.
- Show representative events and source documents with links.
- Keep wording human-readable and avoid internal-only labels.

### Task 5: Verification

**Commands:**
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter tests.test_ai_evidence_graph -v`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task ai-evidence-story-groups`
- Browser check: `http://127.0.0.1:3001/stocks/NVDA`
- `git diff --check`

### Done Criteria

- `/api/ai/evidence-neighborhoods/NVDA` returns `story_groups`.
- `/stocks/NVDA` visibly explains news groups and connection reasons.
- No DB schema, recommendation scoring, paid LLM, vector DB, trading, or scheduler behavior changes.
- Handoff/review contain verification evidence and residual risks.
