# Session Handoff

## Current Status

- 상태: local_verified
- 기준일: 2026-05-22
- 완료:
  - root cause를 확인했다. 새 생성 경로는 막혔지만 기존 `news_event_candidate` artifact는 read model에 남아 `/ai-evidence` 후보 목록에 보일 수 있다.
  - task contract를 생성했다.
  - `/api/events?evidenceType=news_event_candidate` SQL filter에 legacy low-signal topstory suppression을 추가했다.
  - `evidenceType=all` raw 원장은 필터링하지 않는 regression test를 추가했다.
- 막힌 점:
  - 없음.

## Planned Fix

- `/api/events?evidenceType=news_event_candidate` SQL filter에 legacy low-signal topstory suppression을 추가한다.
- `rss_news:marketwatch-topstories`라도 직접 종목이 있으면 유지한다.
- `evidenceType=all` raw 원장은 건드리지 않는다.

## Verification Log

- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter -v`
- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task news-ai-legacy-candidate-read-filter`
- PENDING: EC2 API smoke

## Remaining

- Deploy and smoke on EC2.

## Exact Next Step

- exact next step: deploy to EC2, restart FastAPI read server, and verify `/api/events?evidenceType=news_event_candidate` excludes no-symbol topstory rows.
