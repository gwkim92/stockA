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
- Passed on EC2: pulled commit `6dbeeec`, ran `compileall`, `tests.test_frontend_live_adapter`, and `npm run typecheck`.
- Passed on EC2: rebuilt Next.js with `npm run build`, restarted `stockanalysis-frontend-api.service` and `stockanalysis-web.service`, and both services were `active`.
- Passed on EC2: `/api/data-health` returned `open_gate_detail_count=8`.
- Passed on EC2: `/data-health` HTML contains `벤치마크 괴리 검토`, `전문 분석 원천 한계`, `성과 관찰 대기`, `포트폴리오 검토 결정`, and `성숙한 검토 표본 0/10개`.

## Remaining

- The underlying gates remain open until their real conditions are resolved. This task only makes them understandable.
