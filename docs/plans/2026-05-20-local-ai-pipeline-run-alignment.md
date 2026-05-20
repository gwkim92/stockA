# Local AI Pipeline Run Alignment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the free local news-cluster AI evidence runner update the same `event_intelligence_llm_extract` run history that `/data-health` expects for `event-intelligence-weekly`.

**Architecture:** Keep the low-level news RSS cluster evidence report name and local-rules artifact behavior intact. Add an explicit pipeline-name override to the runner so the operations CLI can record scheduler/data-health cadence runs under `event_intelligence_llm_extract`. This fixes operator visibility without changing schema, scoring, provider choice, or scheduler activation.

**Tech Stack:** Python operations CLI, Postgres `ops.pipeline_run`, existing data-health cadence registry, unittest.

---

### Task 1: Record Guardrail

**Files:**
- Create: `docs/tasks/local-ai-pipeline-run-alignment/contract.md`
- Modify: `AGENTS.md`
- Modify: `docs/project-execution-roadmap.md`

**Steps:**
- Record that this is a run-history alignment task, not a new AI model integration.
- Keep Mac LaunchAgents/`launchctl`, broker/order flow, scoring, schema, and paid provider changes out of scope.

### Task 2: Add Pipeline Name Override

**Files:**
- Modify: `src/stockanalysis/ingest/news/cluster_evidence.py`
- Modify: `src/stockanalysis/operations/cli.py`
- Test: `tests/test_news_rss_cluster_evidence.py`
- Test: `tests/test_data_operations_cli.py`

**Steps:**
- Add a `pipeline_name` argument to `run_news_rss_cluster_evidence`.
- Keep the default as `news_rss_cluster_evidence` for direct/legacy calls.
- Have `stockanalysis-operations news-rss-cluster-evidence-run` pass `event_intelligence_llm_extract` so data-health sees the weekly AI job as current.

### Task 3: Verify and Runtime Check

**Files:**
- Create: `scripts/verify_local_ai_pipeline_run_alignment.sh`
- Create: `docs/tasks/local-ai-pipeline-run-alignment/handoff.md`
- Create: `docs/tasks/local-ai-pipeline-run-alignment/review.md`

**Steps:**
- Run focused unit tests.
- Run the operations command once against local runtime env.
- Confirm `/api/data-health` reports the AI run as current through the expected cadence row.
