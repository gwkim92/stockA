# cycle-ai-syndicated-duplicate-merge-v1 Handoff

## Current Status

- status: in_progress
- in progress: root cause identified; implementation and EC2 verification pending.
- current status: root cause confirmed; merge cleanup implementation is being verified locally and against EC2 rollback SQL.

## Current Evidence

- EC2 `/api/data-health.cycle_ai_quality_audit.status=attention_required`.
- `issue_count=1`, `duplicate_title_count=1`.
- Duplicate title: `Here’s the real story behind the record drop in America’s oil reserves`.
- Source documents:
  - `document_id=13229`, MarketWatch URL, `event_id=2011`, cluster artifacts present.
  - `document_id=13852`, Yahoo Finance mirror URL, `event_id=2634`, AI event candidate present.
- Both events have downstream classification and propagated impact rows, so the old empty-duplicate cleanup skips them by design.

## Decision

- Extend the existing duplicate title cleanup runner to perform a safe canonical merge for syndicated mirrors instead of adding a one-off manual SQL repair.
- Add the cleanup step to `news-intraday` after AI evidence and before propagation/eval so future mirrors are reduced before they inflate propagated impact counts.

## Guardrails

- Recommendation weights, benchmark, portfolio positions, and broker/order boundary must remain unchanged.
- The cleanup must report counts and write through the existing `stockanalysis-operations` backend boundary.

## Next Step

- exact next step: finish local verification, deploy to EC2, execute duplicate cleanup, rerun cycle AI quality audit, and confirm `/api/data-health.open_gates=[]`.
