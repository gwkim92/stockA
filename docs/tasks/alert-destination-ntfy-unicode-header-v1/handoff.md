# alert-destination-ntfy-unicode-header-v1 Handoff

## Current Status

- in progress: local implementation and local verification are complete; EC2 deploy/smoke is pending.
- current status: local implementation and local verification are complete; EC2 deploy/smoke is pending.

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

## Remaining Risks

- EC2 `alert-destination-test-run --execute` still needs to be rerun after deploy to refresh the status artifact.
- The destination URL/topic remains repo-outside and is intentionally not printed or committed.

## Next Step

- exact next step: run AWH verify, commit/push, deploy to EC2, execute `alert-destination-test-run --execute`, and confirm `/api/data-health.open_gates=[]`.
