# Session Handoff

## Current Status

- 상태: local_verified
- 기준일: 2026-05-22
- 완료:
  - task contract를 생성했다.
  - event list SQL을 quality prefilter와 visible rows로 분리했다.
  - API summary에 `suppressed_low_signal_candidate_count`를 추가했다.
  - `/events`, `/ai-evidence`에서 숨긴 저신호 후보 수와 이유를 한국어로 표시했다.
- 막힌 점:
  - 없음.

## Planned Fix

- event list SQL을 `quality prefilter`와 `visible rows`로 분리해 숨긴 후보 수를 계산한다.
- API summary에 `suppressed_low_signal_candidate_count`를 추가한다.
- `/events`, `/ai-evidence`에서 숨김 기준을 한국어로 설명한다.

## Verification Log

- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter -v`
- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task event-candidate-quality-summary`
- PENDING: EC2 API smoke

## Remaining

- Deploy to EC2, restart FastAPI/Next, and verify the new summary field through the live API and pages.

## Exact Next Step

- exact next step: push, pull on EC2, rebuild/restart web, and smoke `/api/events?evidenceType=news_event_candidate`.
