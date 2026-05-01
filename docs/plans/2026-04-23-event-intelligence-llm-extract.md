# Event Intelligence LLM Extract Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** SEC raw filing artifact에서 bounded document chunk를 만들고 structured LLM-style event output을 `ai.*` audit tables와 canonical `event.*` tables에 저장하는 `event-intelligence-llm-extract` 경로를 만든다.

**Architecture:** 기존 heuristic `sec-filings-event-extract`는 유지하고, AI 기반 추출은 별도 CLI로 추가한다. 이번 단계는 live provider credential 없이 fixture provider로 구조화 output, token/cost metadata, extraction artifact, canonical event write를 검증하고, live OpenAI Responses API adapter는 같은 provider boundary에 후속으로 붙인다.

**Tech Stack:** Python 3, Postgres via `psql`, unittest, Docker verification scripts, OpenAI-compatible provider boundary, Structured Outputs-style JSON fixtures

---

### Task 1: task boundary와 문서 고정

**Files:**
- Create: `docs/plans/2026-04-23-event-intelligence-llm-extract.md`
- Create: `docs/tasks/event-intelligence-llm-extract/contract.md`
- Create: `docs/tasks/event-intelligence-llm-extract/plan.md`
- Create: `docs/tasks/event-intelligence-llm-extract/handoff.md`
- Create: `docs/tasks/event-intelligence-llm-extract/review.md`

**Step 1: Contract**

- Include SEC raw filing to AI artifact to canonical event path.
- Exclude live API credentials, trade recommendation, recommendation score changes, and production vector retrieval.

**Step 2: Handoff**

- Keep previous data pipeline context visible: ingest collectors, market universe, price backfill, strategy universe slicing remain foundations.

### Task 2: AI event extraction runner

**Files:**
- Create: `src/stockanalysis/ingest/sec/ai_event_extract.py`
- Modify: `src/stockanalysis/ingest/cli.py`
- Create: `tests/test_sec_ai_event_extract.py`
- Modify: `tests/test_ingest_cli.py`
- Create: `tests/fixtures/llm_sec_event_aapl_10k_structured.json`

**Step 1: Tests first**

- Validate fixture response parsing.
- Validate confidence threshold rejection.
- Validate SQL renderers for prompt template, chunk, invocation, artifact.
- Validate runner creates pipeline run, model invocation, extraction artifact, canonical event write, and success status.
- Validate CLI prints summary.

**Step 2: Implementation**

- Load SEC source document record using existing lookup.
- Read raw artifact and create bounded chunk.
- Upsert `ai.prompt_template`.
- Upsert `ai.document_chunk`.
- Load fixture structured output.
- Insert `ai.model_invocation`.
- Insert `ai.extraction_artifact`.
- Convert validated output to `SecExtractedEventCandidate`.
- Reuse `render_sec_event_extract_sql` for canonical event upsert.
- Mark pipeline run succeeded or failed.

### Task 3: integration verify and docs

**Files:**
- Create: `scripts/verify_event_intelligence_llm_extract.sh`
- Create: `docs/event-intelligence-llm-extract.md`
- Modify: `README.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/ai-intelligence-architecture.md`
- Modify: `docs/tasks/event-intelligence-llm-extract/handoff.md`
- Modify: `docs/tasks/event-intelligence-llm-extract/review.md`

**Step 1: Docker verify**

- Run migrations and seeds.
- Upsert SEC filing metadata.
- Attach raw filing artifact.
- Run `event-intelligence-llm-extract` with fixture provider.
- Assert one canonical event, one model invocation, one document chunk, one extraction artifact, latest run status succeeded.

**Step 2: Final verification**

Run:

```bash
python3 -m compileall src tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
bash -n scripts/verify_event_intelligence_llm_extract.sh
bash scripts/verify_event_intelligence_llm_extract.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task event-intelligence-llm-extract
rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S
```
