# news-ai-eval-cadence-visibility-v1 Review

## Review Notes

- Implemented, deployed to EC2, and smoke-verified.
- Added `news-ai-eval-intraday` cadence and `news-ai-eval` orchestrator step.
- Added read-only data-health payload for latest `news_ai_extraction_quality` eval artifact.
- Added Korean `/data-health` section for AI regression quality and case-level failure visibility.
- Added `ops.pipeline_run` recording around `news-ai-eval-run --execute`, including success and failure status updates. This fixes the operational gap where a passed `ai.eval_run` still appeared as `missing` in data-health pipeline history.
- Guardrails preserved: no recommendation score weight changes, no broker/order path, no canonical event mutation, no paid/external LLM call for this eval.

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_ai_eval tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_frontend_live_adapter`
- Passed: `cd apps/web && npm run typecheck`
- Passed: `cd apps/web && npm run build`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- Passed dry-run: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m stockanalysis.operations.cli news-ai-eval-run --dry-run`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`
- Passed: `bash scripts/verify_project_execution_roadmap.sh`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task news-ai-eval-cadence-visibility-v1`
- EC2 passed: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m compileall -q src tests`
- EC2 passed: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_news_ai_eval tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_frontend_live_adapter`
- EC2 direct execute smoke: `news-ai-eval-run --provider fixture --execute` returned `run_id=1682`, `eval_run_id=39`, `overall_pass=true`, `case_count=5`, `failed_case_count=0`.
- EC2 profile smoke: `operating-data-run --profile news-intraday --execute` returned `run_status=completed`, `failed_step_count=0`; `news-ai-eval` artifact was `succeeded`.
- EC2 API smoke: `/api/data-health` returned `news_ai_eval_quality.status=passed`, `eval_run_id=eval-run-44`, `pipeline_status=succeeded`, `pipeline_health=ok`, `pipeline_run_id=pipeline-run-1701`, and `news_eval_gate_present=false`.
- EC2 route smoke: `/data-health` renders `AI 회귀평가 통과`, `기준 정답 뉴스 세트`, and `뉴스 AI 추출 품질`.

## Remaining

- Longer-horizon AI quality drift history is still future work. This task adds the visible scheduled regression gate and current fixture/gold pass/fail evidence, not a longitudinal drift model.
- Overall `/data-health` remains `attention_required` because other gates are open, including benchmark drift/source gap review. The news AI eval gate itself is no longer open.
