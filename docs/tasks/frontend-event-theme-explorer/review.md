# Review Notes

## Scope Review

- 이 작업은 fixture-backed read-only event/theme explorer로 제한한다.
- Event write APIs, live DB adapter, AI prompt regeneration, auth/RBAC는 변경하지 않는다.

## Verification Evidence

- `npm run typecheck` in `apps/web`: exit 0.
- `bash scripts/verify_frontend_api_contract.sh`: exit 0.
- `bash scripts/verify_frontend_fixture_server.sh`: first sandbox run failed due local port bind permission; approved rerun exit 0.
- `bash scripts/verify_frontend_detail_routes.sh`: exit 0; Next production build included dynamic routes `/events` and `/themes/[themeKey]`, and route HTML smoke checked `/events` plus `/themes/ANNUAL_REPORTING`.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-event-theme-explorer`: exit 0.
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: no output.

## Residual Risks

- production visual QA와 live source freshness는 별도 작업이다.
- current route supports one fully populated theme fixture.
- read-only fixture contract does not yet prove production DB latency, pagination, auth, or freshness behavior.
