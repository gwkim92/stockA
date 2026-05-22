# Session Handoff

## Current Status

- 상태: ec2_verified
- 기준일: 2026-05-22
- 완료:
  - root cause를 확인했다. 새 생성 경로는 막혔지만 기존 `news_event_candidate` artifact는 read model에 남아 `/ai-evidence` 후보 목록에 보일 수 있다.
  - task contract를 생성했다.
  - `/api/events?evidenceType=news_event_candidate` SQL filter에 legacy low-signal topstory suppression을 추가했다.
  - `evidenceType=all` raw 원장은 필터링하지 않는 regression test를 추가했다.
  - EC2에 `9863a22`를 배포하고 FastAPI read server를 재시작했다.
  - EC2 API smoke에서 `marketwatch-topstories` + no-symbol candidate shape가 0건임을 확인했다.
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
- PASS: EC2 `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter -v`
- PASS: EC2 FastAPI service active after restart
- PASS: EC2 `/api/events?asOfDate=2026-05-22&eventType=all&evidenceType=news_event_candidate&limit=50`
  - `item_count=20`
  - `summary_event_count=20`
  - `blocked_shape_count=0`
  - 직접 종목이 붙은 MarketWatch candidate 예: `ELF`는 유지된다.

## Remaining

- 더 넓은 source 품질 점수화와 provider별 confidence tuning은 다음 작업 범위다.
- 기존 artifact row는 삭제하지 않았으므로 raw ledger 또는 직접 링크에서는 보존된다.

## Exact Next Step

- exact next step: continue broader evidence quality work by adding source-level quality scoring or UI-level explanation for hidden low-signal candidates.
