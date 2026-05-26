# source-blocked-recommendation-guardrail-v1 Review

## Review Summary

- Completed. The guardrail is applied at the read DTO boundary, so historical recommendation rows and score weights remain unchanged while source-blocked recommendations become visibly non-usable for professional decision, paper validation input, and any future order path.

## Issues Found

- No local or EC2 regressions found in focused frontend live adapter tests and route smoke.

## Residual Risks

- This does not make EROK financially coverable. EROK still requires a supported periodic filing or a safe prospectus/pro-forma parser.
- `/api/data-health` still reports `professional_source_gap_attention` because the underlying source blocker is real; this is now guarded but not remediated.
- `/api/data-health` also still reports `benchmark_drift_quality_attention`; this is the recommended next task area.
- Live broker submit remains out of scope and disabled.

## Verification Evidence

- Local: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests` passed.
- Local: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter` passed, 65 tests.
- Local: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter tests.test_data_operations_cli` passed, 149 tests.
- Local: `cd apps/web && npm run typecheck` passed.
- Local: `cd apps/web && npm run build` passed.
- Local: `bash scripts/verify_project_execution_roadmap.sh` passed.
- Local: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task source-blocked-recommendation-guardrail-v1` passed.
- EC2: deployed commit `da93536`.
- EC2: compileall, `tests.test_frontend_live_adapter`, `npm run typecheck`, and `npm run build` passed.
- EC2: `/api/recommendations/recommendation-67` returned `source_data_blocked`, `blocked=true`, and `paper_validation_input_allowed=false`.
- EC2: `/api/data-health` returned `guarded_source_blocked_recommendation_count=1` and EROK `active_recommendation_professional_use_blocked=true`.
- EC2 route smoke: `/`, `/data-health`, `/stocks/EROK`, `/recommendations/recommendation-67` returned `200`.
