# AI Intelligence Architecture Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 2026-04-23 기준 최신 AI/RAG/온톨로지/토큰 절감 전략을 프로젝트의 공식 AI intelligence architecture로 고정하고, 이를 감사 가능한 DB boundary와 검증 스크립트로 연결한다.

**Architecture:** AI는 추천 결정자가 아니라 문서 이해, 이벤트 구조화, thesis/review/report 생성을 담당하는 intelligence layer로 둔다. canonical Postgres state, raw artifact store, AI audit metadata, vector/graph adapter를 분리하고, 초기 GraphRAG/ontology는 full graph DB가 아니라 Postgres graph tables 위에서 시작한다.

**Tech Stack:** Postgres, bash verification scripts, Python unittest, Docker Postgres, OpenAI-compatible model gateway design, hybrid RAG and ontology design

---

### Task 1: 최신 AI 설계 근거와 task boundary 고정

**Files:**
- Create: `docs/plans/2026-04-23-ai-intelligence-architecture.md`
- Create: `docs/tasks/ai-intelligence-architecture/contract.md`
- Create: `docs/tasks/ai-intelligence-architecture/plan.md`
- Create: `docs/tasks/ai-intelligence-architecture/handoff.md`
- Create: `docs/tasks/ai-intelligence-architecture/review.md`

**Step 1: Confirm source baseline**

- Open official OpenAI model, prompt caching, retrieval, structured output, function calling, batch, eval, embedding docs.
- Open Microsoft GraphRAG and W3C RDF/OWL/SHACL primary sources.
- Record the project-specific interpretation rather than copying vendor examples.

**Step 2: Write task contract**

- Include AI architecture, token governance, data management, RAG vs ontology decision.
- Exclude live LLM calls, provider credentials, trading automation, production vector DB.

### Task 2: AI architecture document

**Files:**
- Create: `docs/ai-intelligence-architecture.md`
- Modify: `docs/ai-role-map.md`
- Modify: `README.md`

**Step 1: Describe AI entry points**

- Document intelligence
- Event intelligence
- Theme and sector mapping
- Thesis and review
- Research copilot

**Step 2: Document RAG and ontology decision**

- Use hybrid RAG plus ontology/knowledge graph.
- Keep initial implementation in Postgres tables and adapter metadata.
- Defer full graph DB or RDF stack until scale and query patterns justify it.

**Step 3: Document token and quality gates**

- Model routing
- Prompt caching
- Batch processing
- Context minimization
- Structured output validation
- Evidence and eval requirements

### Task 3: AI metadata schema

**Files:**
- Create: `db/migrations/0005_ai_intelligence.sql`
- Modify: `docs/db-schema-design.md`

**Step 1: Add AI schema migration**

- Add `ai.prompt_template`
- Add `ai.model_invocation`
- Add `ai.document_chunk`
- Add `ai.embedding_index`
- Add `ai.extraction_artifact`
- Add `ai.eval_run`

**Step 2: Keep raw payloads out of Postgres**

- Store full raw documents in artifact storage.
- Store chunk hash, token count, short preview, metadata, and vector pointer in Postgres.

### Task 4: Verification wiring

**Files:**
- Create: `scripts/verify_ai_intelligence_architecture.sh`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/ai-intelligence-architecture/handoff.md`
- Modify: `docs/tasks/ai-intelligence-architecture/review.md`

**Step 1: Add Docker integration verify**

- Compile source and tests.
- Run the full unittest suite.
- Apply all migrations and seeds to Docker Postgres.
- Assert all AI schema tables exist.
- Insert prompt, invocation, chunk, embedding, extraction artifact, eval rows.

**Step 2: Run verification**

Run:

```bash
python3 -m compileall src tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
bash -n scripts/verify_ai_intelligence_architecture.sh
bash scripts/verify_ai_intelligence_architecture.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task ai-intelligence-architecture
rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S
```

Expected:

- compile succeeds
- unittest suite passes
- shell syntax check succeeds
- Docker verify creates and validates AI metadata rows
- harness readiness check passes
- placeholder search returns no matches
