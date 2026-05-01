# Review Notes

## Scope Review

- 이 작업은 fixture-backed read-only evidence drilldown으로 제한한다.
- LLM 호출, prompt regeneration, review-note mutation, auth/RBAC, live DB adapter는 변경하지 않는다.

## Verification Evidence

- `bash scripts/verify_frontend_api_contract.sh`: 통과
- `npm run typecheck` in `apps/web`: 통과
- `bash scripts/verify_frontend_detail_routes.sh`: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-ai-evidence-route`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음
- Playwright `http://127.0.0.1:3000/ai-evidence/sec-event-aapl-10k-20240928`: title `AI Evidence | Stockanalysis Dashboard`, console errors 0, warnings 0.
- Playwright `http://127.0.0.1:3000/source-documents/aapl-2024-10k-20240928`: title `Source Document | Stockanalysis Dashboard`, console errors 0, warnings 0.

## Residual Risks

- Production visual QA is not captured; production route/build smoke is covered by `scripts/verify_frontend_detail_routes.sh`.
- The route is fixture-only and supports one known SEC event/source document pair.
- Live source freshness and raw document access control remain separate tasks.
