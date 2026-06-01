# cycle-ai-syndicated-duplicate-merge-v1 Handoff

## Current Status

- status: completed
- completed: syndicated duplicate merge, Nasdaq proxy grounding alignment, EC2 cleanup, EC2 audit refresh, and `/api/data-health` verification are complete.
- current status: EC2 `/api/data-health` is healthy with `open_gates=[]`.

## Current Evidence

- EC2 `/api/data-health.cycle_ai_quality_audit.status=attention_required`.
- `issue_count=1`, `duplicate_title_count=1`.
- Duplicate title: `Here’s the real story behind the record drop in America’s oil reserves`.
- Source documents:
  - `document_id=13229`, MarketWatch URL, `event_id=2011`, cluster artifacts present.
  - `document_id=13852`, Yahoo Finance mirror URL, `event_id=2634`, AI event candidate present.
- Both events have downstream classification and propagated impact rows, so the old empty-duplicate cleanup skips them by design.
- Post-merge cleanup evidence: `cycle-ai-duplicate-title-cleanup-run`, `run_id=2627`, `candidate_count=1`, `merged_classification_count=1`, `deleted_conflicting_classification_count=1`, `merged_propagated_count=2`, `deleted_conflicting_propagated_count=2`, `merged_hierarchical_count=6`, `deleted_conflicting_hierarchical_count=2`, `merged_chunk_count=1`, `merged_artifact_count=1`, `deleted_event_count=1`, `deleted_document_count=1`.
- Post-audit evidence: `cycle-ai-quality-audit-run`, `run_id=2629`, `audit_status=ok`, `audit_score=100`, `issue_count=0`, `duplicate_title_count=0`, `ungrounded_direct_ticker_count=0`, `macro_false_ticker_count=0`, `quantum_energy_mislink_count=0`.

## Decision

- Extend the existing duplicate title cleanup runner to perform a safe canonical merge for syndicated mirrors instead of adding a one-off manual SQL repair.
- Add the cleanup step to `news-intraday` after AI evidence and before propagation/eval so future mirrors are reduced before they inflate propagated impact counts.
- Align QQQ source grounding aliases with the rule enrichment policy by accepting `nasdaq` as a curated QQQ proxy term in both quality audit and AI validator grounding.

## Verification Log

- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cycle_ai_quality_audit tests.test_operating_data_orchestrator -v`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cycle_ai_quality_audit tests.test_news_rss_ai_extract tests.test_operating_data_orchestrator -v`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task cycle-ai-syndicated-duplicate-merge-v1`
- passed: EC2 rollback SQL preview/execute check found one candidate and one safe merge without committing writes.
- passed: EC2 focused tests and compileall on commit `2967637`.
- passed: EC2 `/api/data-health` returned `overall_status=healthy`, `open_gates=[]`, `cycle_ai_quality_audit.status=ok`, `data_operations_artifact_runner.attention_required=false`.
- passed: EC2 manual `stockanalysis-operating-data-news-intraday.service` profile smoke after deployment returned `Result=success`, `ExecMainStatus=0`, generated profile report at `2026-06-01T08:18:12Z`, `run_status=completed`, `failed_step_count=0`, and all 10 steps succeeded including `cycle-ai-duplicate-title-cleanup`.
- passed: Profile cleanup step artifact `/opt/stockanalysis/artifacts/data-operations/20260601T081843Z_event-intelligence-weekly-2/stdout.txt` returned `run_id=2637`, `candidate_count=0`, `deleted_event_count=0`, `deleted_document_count=0`, `recommendation_scoring_mutated=false`, `broker_submit_allowed=false`.
- passed: Post-profile `/api/data-health` still returned `overall_status=healthy`, `open_gates=[]`, `duplicate_title_count=0`, `ungrounded_direct_ticker_count=0`, `macro_false_ticker_count=0`, `quantum_energy_mislink_count=0`.

## Guardrails

- Recommendation weights, benchmark, portfolio positions, and broker/order boundary must remain unchanged.
- The cleanup must report counts and write through the existing `stockanalysis-operations` backend boundary.

## Next Step

- exact next step: continue normal scheduler monitoring; if the next timer-created `news-intraday` run reopens duplicate title count, inspect the new duplicate sample before changing scoring, recommendation, or broker boundaries.
