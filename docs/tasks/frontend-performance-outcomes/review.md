# Review Notes

## Scope Review

- 이 작업은 fixture-backed read-only performance outcome explorer로 제한한다.
- DB schema, benchmark, outcome/attribution 산식, AI generation, auth/RBAC는 변경하지 않는다.

## Verification Evidence

- `npm run typecheck` in `apps/web`: exit 0.
- `python3 -m json.tool docs/api/frontend/contract-index.json`: exit 0.
- `python3 -m json.tool docs/api/frontend/examples/performance-outcomes.json`: exit 0.
- `bash scripts/verify_frontend_api_contract.sh`: exit 0.
- `bash scripts/verify_frontend_fixture_server.sh`: exit 0.
- `bash scripts/verify_frontend_detail_routes.sh`: exit 0; Next production build listed `/performance`, and route HTML smoke checked `Performance outcome review`.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-performance-outcomes`: exit 0.
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: no output.

## Residual Risks

- production visual QA와 live source freshness는 별도 작업이다.
- v1 attribution은 simplified methodology이므로 full attribution 의미로 확대 해석하면 안 된다.
- current route supports one measured recommendation/thesis fixture only.
