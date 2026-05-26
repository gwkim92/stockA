# source-blocked-recommendation-guardrail-v1 Review

## Review Summary

- Local implementation is complete. The guardrail is applied at the read DTO boundary, so historical recommendation rows and score weights remain unchanged while source-blocked recommendations become visibly non-usable for professional decision, paper validation input, and any future order path.

## Issues Found

- No local regressions found in focused frontend live adapter tests.
- EC2 runtime verification is still pending until deployment.

## Residual Risks

- This does not make EROK financially coverable. EROK still requires a supported periodic filing or a safe prospectus/pro-forma parser.
- `/api/data-health` can still report `professional_source_gap_attention` because the underlying source blocker is real; this task only prevents active recommendations from appearing professionally usable.
- Live broker submit remains out of scope and disabled.

## Verification Evidence

- Local: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests` passed.
- Local: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter` passed, 65 tests.
- Local: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter tests.test_data_operations_cli` passed, 149 tests.
- Local: `cd apps/web && npm run typecheck` passed.
- Local: `cd apps/web && npm run build` passed.
- Local: `bash scripts/verify_project_execution_roadmap.sh` passed.
- Local: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task source-blocked-recommendation-guardrail-v1` passed.
