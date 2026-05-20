# AI News Cluster Map Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 저장된 `news_cluster_summary` AI artifact와 RSS chunk/index 상태를 read-only API와 `/intelligence` 화면에 노출한다.

**Architecture:** FastAPI/frontend live adapter는 canonical Postgres에서 `ai.extraction_artifact`, `ai.model_invocation`, `ingest.source_document`, `ai.document_chunk`, `ai.embedding_index`를 read-only로 조회한다. Next.js `/intelligence`는 기존 이벤트 기반 묶음과 함께 저장된 AI 뉴스 묶음, 연결 종목, 원천 문서, RAG 준비 상태를 표시한다.

**Tech Stack:** Python live adapter SQL renderer, unittest, Next.js Server Components, TypeScript DTO, existing frontend API client.

---

### Task 1: Task Contract

**Files:**
- Create: `docs/tasks/ai-news-cluster-map/contract.md`
- Create: `docs/tasks/ai-news-cluster-map/handoff.md`
- Create: `docs/tasks/ai-news-cluster-map/review.md`

**Steps:**
- Define scope as read-only API/UI only.
- Exclude schema migration, paid news API, live LLM, recommendation scoring, and trading writes.
- Record verification commands.

### Task 2: Backend API

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Modify: `src/stockanalysis/frontend/pagination.py`
- Test: `tests/test_frontend_live_adapter.py`

**Steps:**
- Add `/api/ai/news-clusters`.
- Add `render_frontend_ai_news_cluster_list_state_sql`.
- Build DTO with summary, clusters, extraction run, cluster events, source documents, chunk and embedding counts.
- Ensure no vector URI, DB URL, or secret is exposed.

### Task 3: Frontend UI

**Files:**
- Modify: `apps/web/src/lib/types.ts`
- Modify: `apps/web/src/lib/frontend-api.ts`
- Modify: `apps/web/src/app/intelligence/page.tsx`

**Steps:**
- Add `AiNewsClusterListData`.
- Add `getAiNewsClusters()`.
- Fetch news clusters in parallel with existing page data.
- Render a stored AI analysis board before the derived event grouping.

### Task 4: Verification

**Files:**
- Create: `scripts/verify_ai_news_cluster_map.sh`
- Modify: `docs/verification-plan.md`
- Update: task handoff/review.

**Steps:**
- Run targeted backend tests.
- Run `npm run typecheck` and `npm run build`.
- Run live FastAPI smoke for `/api/ai/news-clusters`.
- Browser-check `/intelligence`.
- Run AWH and `git diff --check`.
