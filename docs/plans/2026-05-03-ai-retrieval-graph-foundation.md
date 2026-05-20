# AI Retrieval Graph Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the minimal retrieval and evidence graph foundation so AI features can cite stored evidence without introducing premature graph/vector/orchestration platforms.

**Architecture:** Keep Postgres as the canonical system of record. Add internal adapter boundaries before selecting pgvector, OpenAI vector stores, external vector DB, Neo4j, RDF, GraphRAG, or Dagster. Use existing `ref.classification_*`, `event.event_*_impact`, `signal.thesis*`, `portfolio.*`, and `ai.*` metadata first.

**Tech Stack:** Python 3.11, Postgres SQL, psycopg command executor pattern, `unittest`, existing shell verification scripts.

---

### Task 1: Confirm Scope And Ownership

**Files:**
- Read: `docs/tasks/ai-retrieval-graph-foundation/contract.md`
- Read: `docs/ai-intelligence-architecture.md`
- Read: `docs/project-execution-roadmap.md`
- Read: `AGENTS.md`

**Step 1: Check active worktree**

Run:

```bash
git status --short
```

Expected: any active frontend/API immediate-task changes are treated as out of scope and not modified.

**Step 2: Confirm immediate task order**

Run:

```bash
rg -n 'Current task:|If AI work is requested|현재 고정된 immediate next task' docs/project-execution-roadmap.md AGENTS.md
```

Expected: immediate next task remains unchanged from AGENTS and `docs/project-execution-roadmap.md`.

**Step 3: Commit only after real implementation**

Do not commit this plan alone unless the user explicitly asks for documentation-only commit.

### Task 2: Define Retrieval Boundary

**Files:**
- Create: `src/stockanalysis/ai/__init__.py`
- Create: `src/stockanalysis/ai/retrieval.py`
- Test: `tests/test_ai_retrieval.py`
- Modify if needed: `pyproject.toml`

**Step 1: Write failing tests**

Test the shape before implementation:

```python
from stockanalysis.ai.retrieval import RetrievalQuery, RetrievalResult, InMemoryRetrievalAdapter


def test_in_memory_retrieval_adapter_returns_matching_chunk():
    adapter = InMemoryRetrievalAdapter(
        [
            RetrievalResult(
                chunk_id=1,
                document_id=10,
                score=0.91,
                text_preview="annual report risk factors",
                source_uri="adapter://test/document/10/chunk/0",
            )
        ]
    )

    results = adapter.search(RetrievalQuery(text="risk factors", limit=5))

    assert [item.chunk_id for item in results] == [1]
```

**Step 2: Run test to verify it fails**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_ai_retrieval -v
```

Expected: FAIL because `stockanalysis.ai.retrieval` does not exist.

**Step 3: Implement minimal interface**

Add dataclasses for `RetrievalQuery` and `RetrievalResult`, plus a fake adapter for deterministic tests. Do not add production vector dependencies.

**Step 4: Run test to verify it passes**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_ai_retrieval -v
```

Expected: PASS.

### Task 3: Define Evidence Neighborhood Query

**Files:**
- Create or modify: `src/stockanalysis/ai/evidence_graph.py`
- Test: `tests/test_ai_evidence_graph.py`

**Step 1: Write SQL rendering tests**

Test that the query joins existing tables instead of requiring a graph DB:

```python
from stockanalysis.ai.evidence_graph import render_instrument_evidence_neighborhood_sql


def test_evidence_neighborhood_uses_existing_graph_tables():
    sql = render_instrument_evidence_neighborhood_sql(primary_symbol="AAPL", as_of_date="2024-11-01")

    assert "ref.classification_node" in sql
    assert "event.event_classification_impact" in sql
    assert "event.event_instrument_impact" in sql
    assert "signal.thesis" in sql
```

**Step 2: Run test to verify it fails**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_ai_evidence_graph -v
```

Expected: FAIL because the module does not exist.

**Step 3: Implement minimal query renderer**

Use existing SQL literal helpers where available. Return JSON text from SQL for compatibility with current command executor patterns.

**Step 4: Run targeted tests**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_ai_evidence_graph -v
```

Expected: PASS.

### Task 4: Add Ontology-Lite Validation Checks

**Files:**
- Create or modify: `src/stockanalysis/ai/ontology_validation.py`
- Test: `tests/test_ai_ontology_validation.py`

**Step 1: Write failing tests for SQL checks**

Cover:
- orphan classification edges
- invalid relation type
- overlapping validity windows
- inferred membership without source evidence or confidence

**Step 2: Run test to verify it fails**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_ai_ontology_validation -v
```

Expected: FAIL until module exists.

**Step 3: Implement SQL renderers only**

Keep this as read-only validation. Do not add migrations unless a separate schema task approves it.

**Step 4: Run targeted tests**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_ai_ontology_validation -v
```

Expected: PASS.

### Task 5: Add Verification Script

**Files:**
- Create: `scripts/verify_ai_retrieval_graph_foundation.sh`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/ai-retrieval-graph-foundation/handoff.md`
- Modify: `docs/tasks/ai-retrieval-graph-foundation/review.md`

**Step 1: Add script syntax and unit checks**

The first script version should run syntax and targeted tests only:

```bash
bash -n scripts/verify_ai_retrieval_graph_foundation.sh
PYTHONPATH=src python3 -m unittest tests.test_ai_retrieval tests.test_ai_evidence_graph tests.test_ai_ontology_validation -v
```

**Step 2: Run verification**

Run:

```bash
bash scripts/verify_ai_retrieval_graph_foundation.sh
```

Expected: PASS.

**Step 3: Update docs with evidence**

Record exact commands and outcomes in `handoff.md` and `review.md`.

### Task 6: Full Regression

**Files:**
- Read: `docs/tasks/ai-retrieval-graph-foundation/contract.md`

**Step 1: Run full unit tests**

Run:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

Expected: PASS.

**Step 2: Run roadmap verification**

Run:

```bash
bash scripts/verify_project_execution_roadmap.sh
```

Expected: PASS and immediate next task remains unchanged.

**Step 3: Run harness verification**

Run:

```bash
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task ai-retrieval-graph-foundation
```

Expected: PASS.

**Step 4: Check formatting**

Run:

```bash
git diff --check
```

Expected: no whitespace errors.

### Task 7: Commit

**Files:**
- Stage only files touched for this task.

**Step 1: Review diff**

Run:

```bash
git diff -- docs/tasks/ai-retrieval-graph-foundation docs/plans/2026-05-03-ai-retrieval-graph-foundation.md docs/ai-intelligence-architecture.md docs/project-execution-roadmap.md
```

Expected: diff contains only retrieval/graph foundation scope.

**Step 2: Stage scoped files**

Run:

```bash
git add docs/tasks/ai-retrieval-graph-foundation docs/plans/2026-05-03-ai-retrieval-graph-foundation.md docs/ai-intelligence-architecture.md docs/project-execution-roadmap.md
```

**Step 3: Commit**

Run:

```bash
git commit -m "docs: define ai retrieval graph foundation"
```

Expected: commit succeeds.
