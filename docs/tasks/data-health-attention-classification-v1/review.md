# data-health-attention-classification-v1 Review

## Review Notes

- Completed locally. The change improves data-health interpretability without suppressing any existing gate.
- `open_gates` remains the compatibility field and still drives `overall_status=attention_required`.
- `open_gate_details` explains each gate in user-facing Korean with what kind of problem it is and what action is expected.
- The frontend now renders the detailed cards before the raw gate chips, so users no longer need to infer meaning from machine-style gate ids.
- No scoring weight, benchmark definition, portfolio position, or broker/order boundary was changed.

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter` (`72 tests`).
- Passed: `cd apps/web && npm run typecheck`.
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`.
- Passed: `bash scripts/verify_project_execution_roadmap.sh`.
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task data-health-attention-classification-v1`.

## Remaining

- EC2 deploy and route/API smoke are still needed before calling the task fully deployed.
- The underlying gates remain open until their real conditions are resolved. This task only makes them understandable.
