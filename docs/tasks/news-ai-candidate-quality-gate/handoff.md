# Session Handoff

## Current Status

- 상태: local_verified
- 기준일: 2026-05-22
- 완료:
  - root cause를 확인했다. `news_event_candidate` 생성 전 후보 조회가 `marketwatch-topstories` 무종목 개인 재무/일반 뉴스를 LLM 후보로 넘기고 있었다.
  - task contract를 생성했다.
  - SQL 후보 조회에서 무종목 `rss_news:marketwatch-topstories` 후보를 제외했다.
  - Python candidate loader에 동일한 품질 게이트를 추가했다.
  - official macro/Fed 무종목 뉴스는 계속 후보로 허용하는 regression test를 추가했다.
- 막힌 점:
  - 없음.

## Planned Fix

- SQL 후보 조회에서 `marketwatch-topstories`이면서 직접 종목이 없는 row를 제외한다.
- Python loader에서도 `UNKNOWN`/`UNCLASSIFIED`/blank symbol과 `marketwatch-topstories` 조합을 제외한다.
- 제외 후보는 dry-run/execute 결과에 나타나지 않아 provider 호출과 artifact 생성을 만들지 않는다.

## Verification Log

- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_ai_extract -v`
- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task news-ai-candidate-quality-gate`
- PENDING: EC2 dry-run smoke

## Remaining

- Commit, push, deploy, and run EC2 dry-run smoke.

## Exact Next Step

- exact next step: deploy to EC2 and run `news-rss-ai-extract-run --dry-run` to confirm noisy MarketWatch topstory candidates are not selected.
