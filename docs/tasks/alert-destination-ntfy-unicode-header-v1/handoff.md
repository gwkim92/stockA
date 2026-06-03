# alert-destination-ntfy-unicode-header-v1 Handoff

## Current Status

- completed: local implementation, local verification, GitHub push, EC2 deploy, EC2 alert test, data-health smoke, and `13000` route smoke are complete.
- current status: EC2 `/api/data-health` is healthy with `open_gates=[]`; `alert_destination.status=external_destination_verified`.

## Root Cause

- `ntfy` 요청의 `Title` header에 한국어 기본 제목이 들어갔다.
- Python `urllib.request.Request`는 header 값을 latin-1 범위로 인코딩하므로 한국어 header가 `UnicodeEncodeError`를 일으켰다.
- 알림 목적지 설정이나 ntfy reachability 문제가 아니라 HTTP header encoding boundary 문제다.

## Changes

- `ntfy` alert header title is now ASCII-safe.
- Non-ASCII alert titles are preserved in the UTF-8 message body instead of being sent as HTTP header bytes.
- Added regression coverage for Korean `ntfy` titles and ASCII title pass-through.

## Verification

- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_alert_destination_free_channel`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: local `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task alert-destination-ntfy-unicode-header-v1`.
- passed: commit `1f2b08f` pushed to `origin/codex/local-mvp-runtime-aws-bootstrap`.
- passed: EC2 pulled commit `1f2b08f`; EC2 `tests.test_alert_destination_free_channel` passed and compileall passed.
- passed: EC2 `stockanalysis-operations alert-destination-test-run --env-file /opt/stockanalysis/runtime/frontend-api.env --execute` wrote `/opt/stockanalysis/artifacts/alert-destination/status.json`.
- passed: alert status artifact reports `status=passed`, `last_test_status=passed`, `last_tested_at=2026-06-03T05:24:55Z`, `destination_type=ntfy`, `http_status_code=200`, `secret_redaction=destination_url_and_tokens_not_recorded`.
- passed: EC2 `/api/data-health` returned `overall_status=healthy`, `open_gates=[]`, `alert_destination.status=external_destination_verified`, `test_recent=true`.
- passed: local tunnel restored with PID `31325`, `127.0.0.1:13000 -> EC2 127.0.0.1:3000`.
- passed: `http://127.0.0.1:13000/`, `/data-health`, `/ai-evidence`, `/intelligence`, and `/cycle-map` returned HTTP 200.

## Remaining Risks

- The destination URL/topic remains repo-outside and is intentionally not printed or committed.
- The alert test freshness gate will reopen after 168 hours unless a periodic alert destination test is added or manually rerun.

## Next Step

- exact next step: continue with user-facing UX/evidence clarity work now that operational gates are closed; if `alert_destination` reopens after 168 hours, rerun or schedule the alert destination test without exposing the ntfy topic.
