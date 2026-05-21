# Review Notes

## Summary

- `/api/recommendations` read-only list endpoint and `/recommendations` Next.js page were added.
- The list shows latest recommendation batch summary, per-symbol score/action, thesis linkage, evidence quality, primary AI/event evidence, and outcome status.
- Navigation now sends users to the recommendation index instead of a hardcoded detail page.

## Verification

- `bash scripts/verify_frontend_api_contract.sh`: pass.
- `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter tests.test_frontend_api_adapter tests.test_frontend_fixture_server -v`: pass.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest tests.test_frontend_api_server -v`: pass.
- `bash scripts/verify_frontend_api_adapter.sh`: pass.
- `bash scripts/verify_frontend_fixture_server.sh`: pass.
- `cd apps/web && npm run build`: pass.
- `cd apps/web && npm run typecheck`: pass after `next build` generated `.next/types`.
- EC2 DB direct SQL smoke: pass.
- EC2 deploy/build/service restart: pass.
- EC2 API smoke for `/api/recommendations`: pass.
- Local tunnel web smoke for `/recommendations`: pass.

## Remaining Risks

- 뉴스 AI 후보별 전용 화면은 아직 개선 여지가 있다.
- This slice does not change scoring, recommendation generation, paper trading, or broker/order flow.
