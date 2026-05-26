# cycle-ai-quality-audit-contamination-remediation-v1 Handoff

## Status

- in progress: task contract and plan are created; implementation has not begun. The first action is evidence gathering from EC2 data-health and audit samples.
- blockers: none known yet.

## Context

- `professional-source-blocker-raw-filing-remediation-v1` completed with EROK durable exclusion.
- `news-intraday-scheduler-failure-remediation-v1` completed; `news-intraday` rerun succeeded and data-health reports `last_result=success`.
- EC2 data-health still reports `cycle_ai_quality_audit.status=attention_required`.
- Latest known issue classes include ungrounded direct tickers, macro false ticker counts, and duplicate title contamination.

## Exact Next Step

- exact next step: pull latest EC2 `/api/data-health` `cycle_ai_quality_audit` samples, choose the highest-impact contamination class, and trace it back to validator/dedupe code before changing anything.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not suppress warnings without fixing or reclassifying the underlying cause.
