# News AI Eval Cadence Visibility V1 Plan

## Summary

Promote the existing fixture/gold news AI evaluation from an ad-hoc CLI into a scheduled quality gate that is visible in data-health. This gives the project a low-cost regression check for AI extraction quality before evidence feeds recommendation and thesis review.

## Implementation

- Add `news-ai-eval-intraday` cadence because the eval guards the intraday news/AI loop and does not call paid providers.
- Add `news-ai-eval` orchestrator step after `news-ai-evidence`.
- Expose latest `news_ai_extraction_quality` `ai.eval_run` on data-health.
- Render pass/fail, case counts, precision metrics, macro false ticker rate, quantum-energy misclassification, and translation availability in Korean.
- Record `ops.pipeline_run` around `news-ai-eval-run --execute` so operational freshness, scheduler history, and the visible eval result agree.

## EC2 Evidence

- Deployed commits: `bf921a1`, `205ebf7`.
- Direct execute smoke: `run_id=1682`, `eval_run_id=39`, `overall_pass=true`.
- `news-intraday` profile smoke: `run_status=completed`, `failed_step_count=0`, latest `news-ai-eval` pipeline `pipeline-run-1701`.
- `/api/data-health`: `news_ai_eval_quality.status=passed`, `eval_run_id=eval-run-44`, `pipeline_health=ok`, no `news_ai_eval_quality_attention` gate.
- `/data-health`: renders `AI 회귀평가 통과`, `기준 정답 뉴스 세트`, and `뉴스 AI 추출 품질`.

## Non-Goals

- No Codex OAuth real batch call in this eval.
- No canonical event mutation.
- No recommendation weight or order changes.
