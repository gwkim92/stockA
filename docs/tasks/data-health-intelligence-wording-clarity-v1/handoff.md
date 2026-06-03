# data-health-intelligence-wording-clarity-v1 Handoff

## Current Status

- completed: local implementation, local verification, AWH verify, GitHub push, EC2 deploy/build/restart, route smoke, Playwright text smoke, and data-health smoke are complete.

## Decisions

- This is a wording/UX clarity task only.
- Preserve `/data-health` as the detailed operational page, but make collapsed technical sections clearly optional.
- Avoid labels that imply a missing manual approval/review control.

## Verification

- passed: local text scan found no `검토 가능`, `별도 검토 가능`, `상세 검토 가능`, `AI 상세`, `운영자용`, or `검토 필요` in `data-health`/`intelligence`.
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- passed: `git diff --check`
- passed: EC2 services are active and internal `/data-health`, `/intelligence`, and `/__health` returned HTTP 200 before deploy.
- passed: local tunnel restored on `127.0.0.1:13000` with ssh PID `61058`.
- passed: commit `5a7d7c3` deployed to EC2; `npm run build` passed and `stockanalysis-web.service` restarted active.
- passed: EC2 internal route smoke returned HTTP 200 for `/data-health` and `/intelligence`.
- passed: Playwright text smoke on `http://127.0.0.1:13000/data-health` returned `hasOldReviewPossible=false` and `hasOpsRecord=true`.
- passed: Playwright text smoke on `http://127.0.0.1:13000/intelligence` returned `hasAiDetail=false`, `hasEvidenceDetail=true`, `hasLedgerText=false`, and `hasPlainNewsText=true`.
- passed: EC2 `/api/data-health` returned `overall_status=healthy`, `open_gates=[]`, `alert_destination.status=external_destination_verified`, `live_ai_invocation_health.status=recovered_with_recent_failures`, and `news_ai_eval_quality.status=passed`.

## Next Step

- exact next step: continue the broader UX audit with `/cycle-map`, `/recommendations`, and `/paper-trading`, focusing on pages that still mix status display, evidence explanation, and action boundary wording.
