# News AI Eval Cadence Visibility V1 Plan

## Summary

Promote the existing fixture/gold news AI evaluation from an ad-hoc CLI into a scheduled quality gate that is visible in data-health. This gives the project a low-cost regression check for AI extraction quality before evidence feeds recommendation and thesis review.

## Implementation

- Add `news-ai-eval-intraday` cadence because the eval guards the intraday news/AI loop and does not call paid providers.
- Add `news-ai-eval` orchestrator step after `news-ai-evidence`.
- Expose latest `news_ai_extraction_quality` `ai.eval_run` on data-health.
- Render pass/fail, case counts, precision metrics, macro false ticker rate, quantum-energy misclassification, and translation availability in Korean.

## Non-Goals

- No Codex OAuth real batch call in this eval.
- No canonical event mutation.
- No recommendation weight or order changes.
