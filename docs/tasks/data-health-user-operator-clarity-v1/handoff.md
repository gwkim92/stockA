# data-health-user-operator-clarity-v1 Handoff

## Current Status

- completed: local implementation, EC2 deployment, route smoke, browser wording smoke, and AWH verification are complete.

## Decisions

- This is a frontend wording and status hierarchy task only.
- Keep current backend payload shape and page layout structure.
- Keep all order and scoring boundaries unchanged.
- Preserve raw operator diagnostics in collapsed details.
- Treat `/data-health` as a status control room: top-level user status first, raw diagnostics in collapsed sections.

## Changes

- Metadata and hero now use `데이터·자동화 상태`.
- Top command panel now says `상태 판정판` instead of an operator-only framing.
- User-facing pipeline copy now uses `보유 상태 판단`, `보유 상태`, `가상 매매`, and `확인 대상`.
- Recommendation copy now says recommendations are detailed evidence to verify, not a human-facing review document.
- `operationCopy()` now normalizes older backend/operator phrases into user-readable wording without renaming raw DTO fields.

## Verification

- passed: source scan found no `보유검토`, `보유 검토`, `검토 후보`, `검토서`, or `페이퍼` in `apps/web/src/app/data-health/page.tsx`.
- passed: `cd apps/web && npm run typecheck`.
- passed: `cd apps/web && npm run build`.
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`.
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`.
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task data-health-user-operator-clarity-v1`.
- passed: EC2 deployed commit `d8a919b`; `npm run typecheck` and `npm run build` passed on `/opt/stockanalysis/app/apps/web`.
- passed: EC2 services active after restart: `stockanalysis-web.service`, `stockanalysis-frontend-api.service`.
- passed: EC2 internal route smoke returned `200` for `/data-health`.
- passed: local tunnel route smoke returned `200` for `http://127.0.0.1:13000/data-health`.
- passed: `/api/data-health` still reports `open_gates=[]`, `alert_destination.status=external_destination_verified`, `news_ai_eval_quality.status=passed`, and `outcome_maturity_wait_monitor.status=managed_wait`.
- passed: Playwright browser text smoke for `/data-health` found zero old terms: `보유검토`, `보유 검토`, `검토 후보`, `검토서`, `페이퍼`.
- passed: Playwright confirmed intended terms: `데이터·자동화 상태`, `상태 판정판`, `보유 상태 판단`, `가상 매매`.

## Next Step

- exact next step: continue the broader UX audit on `/performance` and `/portfolio/coverage`, because outcome/performance and portfolio risk pages are the next places where operator wording can confuse investor-facing interpretation.
