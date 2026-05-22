# Session Handoff

## Current Status

- 상태: local_verified
- 기준일: 2026-05-22
- 완료:
  - root cause를 확인했다. `/events`가 전체 raw event rows를 기본 목록으로 보여주면서 개별 AI 후보, 뉴스 묶음 근거, 미검토 row가 같은 위계로 보였다.
  - 작업 범위와 mutable surface를 `contract.md`에 고정했다.
  - `/events` 기본 목록을 `news_event_candidate` 전용 조회로 바꿨다.
  - 전체 raw 원장은 별도 접힘 영역으로 이동했다.
  - 기본 목록에서 저신뢰, broad theme, `UNKNOWN`/무종목 MarketWatch top story 잡음을 후순위로 내렸다.
  - metric과 문구를 기본 판단 목록, 원장 전체, 뉴스 묶음, 미검토 기준으로 정리했다.
- 막힌 점:
  - 없음.

## Planned Fix

- `/events`에서 `getEvents({ evidenceType: "news_event_candidate" })`를 기본 판단 목록으로 사용한다.
- 낮은 신뢰도, `UNKNOWN`/무종목 broad theme, MarketWatch top story 잡음은 기본 목록에서 제외한다.
- 전체 raw 원장은 `getEvents({ evidenceType: "all" })`로 따로 조회하고 보조 접힘 영역에 둔다.
- metric과 문구는 전체 원장 수와 기본 후보 수를 분리해서 설명한다.

## Verification Log

- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task events-default-decision-scope`
- PENDING: EC2 `/events` render smoke

## Remaining

- EC2 deploy and render smoke.

## Exact Next Step

- exact next step: commit, push, deploy to EC2, then verify `/events` renders with candidate-first copy.
