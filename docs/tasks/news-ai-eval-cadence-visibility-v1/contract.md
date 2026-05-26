# news-ai-eval-cadence-visibility-v1 Contract

## Task Request

- request: Make the existing news AI fixture/gold evaluation a scheduled and visible quality gate rather than an ad-hoc CLI.
- context: The project has Codex OAuth batch news analysis and a fixture `news-ai-eval-run`, but data-health mainly shows live contamination audit. The professional investment goal needs longer-running AI quality evaluation and drift monitoring before AI evidence is trusted as recommendation input.

## Goal

- goal: Add a cadence/orchestrator/data-health visibility path for `news-ai-eval-run` so operators can see whether theme precision, direct ticker grounding, macro-only false ticker rate, quantum-energy misclassification, blocked candidate correctness, and Korean translation availability still pass.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/korean-labels.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `docs/tasks/news-ai-eval-cadence-visibility-v1/*`

## Invariants

- No recommendation score weight changes.
- No broker submit or order flow.
- The evaluation uses fixture/gold dataset by default and does not call paid/external LLM providers.
- This is a read/eval visibility layer; it must not mutate canonical news/event evidence.

## Scope

- Add a data operations cadence entry for `news-ai-eval-run`.
- Add it to the `news-intraday` or decision profile at a safe point after news AI evidence generation.
- Expose latest `ai.eval_run` for `news_ai_extraction_quality` on `/api/data-health`.
- Add Korean data-health UI cards explaining pass/fail and the main metrics.
- Add tests for cadence, orchestrator, live adapter, and frontend type/build coverage.

## Verification

- verification command: focused Python tests for cadence, orchestrator, and live adapter visibility.
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck && npm run build`
- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task news-ai-eval-cadence-visibility-v1`

