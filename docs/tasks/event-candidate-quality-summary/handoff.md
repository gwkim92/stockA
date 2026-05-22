# Session Handoff

## Current Status

- 상태: ec2_verified
- 기준일: 2026-05-22
- 완료:
  - task contract를 생성했다.
  - event list SQL을 quality prefilter와 visible rows로 분리했다.
  - API summary에 `suppressed_low_signal_candidate_count`를 추가했다.
  - `/events`, `/ai-evidence`에서 숨긴 저신호 후보 수와 이유를 한국어로 표시했다.
  - EC2에 `3550c54`를 배포하고 FastAPI/Next를 재시작했다.
  - EC2 live API와 브라우저에서 새 summary/count 문구가 표시됨을 확인했다.
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
- PASS: EC2 `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter -v`
- PASS: EC2 `cd apps/web && npm run build`
- PASS: EC2 services active: `stockanalysis-frontend-api.service`, `stockanalysis-web.service`
- PASS: EC2 live API `/api/events?asOfDate=2026-05-22&eventType=all&evidenceType=news_event_candidate&limit=50`
  - `event_count=20`
  - `suppressed_low_signal_candidate_count=4`
  - `blocked_shape_count=0`
- PASS: Browser smoke `http://127.0.0.1:13000/events`
  - shows `품질 필터 숨김`
  - shows `top story 4개를 숨겼다`
- PASS: Browser smoke `http://127.0.0.1:13000/ai-evidence`
  - shows `품질 필터 숨김`
  - shows `숨긴 후보 4개는 삭제한 것이 아니라`

## Remaining

- `/ai-evidence` still mixes direct stock candidates and macro/no-symbol candidates in the same list. Next task should split macro-only news into a separate “상위 흐름 후보” section instead of making it look like an individual stock candidate.

## Exact Next Step

- exact next step: create a follow-up UI/read-model task that separates direct instrument candidates from macro/theme-only candidates.
