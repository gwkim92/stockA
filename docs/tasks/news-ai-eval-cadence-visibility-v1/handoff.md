# news-ai-eval-cadence-visibility-v1 Handoff

## Status

- completed: local verification, EC2 deployment, EC2 profile smoke, API smoke, and route smoke complete.

## Context

- `news-ai-eval-run` already existed and can score the 기준 정답 뉴스 세트 without external LLM calls.
- Added cadence job `news-ai-eval-intraday` with pipeline `news_ai_extraction_quality`.
- Added `news-ai-eval` to the `news-intraday` operating-data profile immediately after `news-ai-evidence` and before propagation.
- `/api/data-health` now exposes latest `ai.eval_run` where `eval_name=news_ai_extraction_quality` and `dataset_version=news-ai-eval-v1`.
- `/data-health` now shows AI regression pass/fail, case counts, theme precision, direct ticker grounding precision, macro false ticker count, quantum-energy misclassification count, blocked candidate correctness, Korean translation availability, and recent case results.
- `news-ai-eval-run --execute` now records both `ops.pipeline_run` and `ai.eval_run`, so the data-health scheduler table no longer marks a successful eval as missing.
- No recommendation weights, benchmark definitions, canonical event rows, broker submit, or order flow were changed.

## Completion Evidence

- local commit: `bf921a1` added cadence/orchestrator/API/UI visibility.
- local/EC2 fix commit: `205ebf7` added `ops.pipeline_run` recording for `news-ai-eval-run`.
- local focused tests passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_ai_eval tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_frontend_live_adapter`.
- local full tests passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`.
- local frontend checks passed: `cd apps/web && npm run typecheck && npm run build`.
- local roadmap and harness checks passed: `bash scripts/verify_project_execution_roadmap.sh`; `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task news-ai-eval-cadence-visibility-v1`.
- EC2 deploy evidence: `/opt/stockanalysis/app` fast-forwarded to `205ebf7`.
- EC2 focused tests passed: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_news_ai_eval tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_frontend_live_adapter`.
- EC2 direct execute smoke: `news-ai-eval-run --provider fixture --execute` returned `run_id=1682`, `eval_run_id=39`, `overall_pass=true`.
- EC2 `news-intraday` profile smoke completed with `failed_step_count=0`; `news-ai-eval` artifact run succeeded at `pipeline-run-1701` and latest `eval_run_id=44`.
- EC2 `/api/data-health` smoke shows `news_ai_eval_quality.status=passed`, `eval_run_id=eval-run-44`, `case_count=5`, `failed_case_count=0`, `pipeline_status=succeeded`, `pipeline_health=ok`, and no `news_ai_eval_quality_attention` gate.
- EC2 `/data-health` route smoke renders `AI 회귀평가 통과`, `기준 정답 뉴스 세트`, and `뉴스 AI 추출 품질`.

## Exact Next Step

- exact next step: continue the professional-equity-analysis goal by tightening the next weakest gate: recommendation/portfolio outcome history and user-facing professional decision waterfall clarity, while keeping scoring weights and live broker submit blocked.
