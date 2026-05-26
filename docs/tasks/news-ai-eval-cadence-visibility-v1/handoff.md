# news-ai-eval-cadence-visibility-v1 Handoff

## Status

- in progress: local implementation and verification complete; EC2 deployment/smoke pending.

## Context

- `news-ai-eval-run` already existed and can score the 기준 정답 뉴스 세트 without external LLM calls.
- Added cadence job `news-ai-eval-intraday` with pipeline `news_ai_extraction_quality`.
- Added `news-ai-eval` to the `news-intraday` operating-data profile immediately after `news-ai-evidence` and before propagation.
- `/api/data-health` now exposes latest `ai.eval_run` where `eval_name=news_ai_extraction_quality` and `dataset_version=news-ai-eval-v1`.
- `/data-health` now shows AI regression pass/fail, case counts, theme precision, direct ticker grounding precision, macro false ticker count, quantum-energy misclassification count, blocked candidate correctness, Korean translation availability, and recent case results.
- No recommendation weights, benchmark definitions, canonical event rows, broker submit, or order flow were changed.

## Exact Next Step

- exact next step: run full local verification, AWH task verify, then deploy to EC2 and execute `news-ai-eval-run --provider fixture --execute` once so data-health has a live `eval_run_id`.
